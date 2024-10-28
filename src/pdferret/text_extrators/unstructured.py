from typing import Dict

import numpy as np
from pydantic import BaseModel
from unstructured.documents import elements as doc_elements
from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf

from ..base import BaseProcessor
from ..datamodels import ChunkType, MetaInfo, PDFChunk, PDFDoc, PDFError
from ..logging import logger
from ..utils.langdetect import detect_language
from ..utils.utils import split_every


def extract_bbox(coords):
    coords = np.array(coords)
    xmin = coords[:, 0].min()
    xmax = coords[:, 0].max()
    # looks like ther're discrepancy in definining
    # direction of y-axis, some define it pointing up
    # some pointing down
    # according to Apache PDFBox (https://pdfbox.apache.org/download.html)
    # it should be defined pointing up, which is assumed here
    ymax = 1 - coords[:, 1].min()
    ymin = 1 - coords[:, 1].max()
    return (xmin, xmax, ymin, ymax)


class UnstructuredTextExtractor(BaseProcessor):
    parallel = "process"
    operates_on = PDFDoc

    def __init__(self, strategy="auto", languages=("eng",), min_text_len=20, batch_size=None, n_proc=None):
        """
        strategy, languages - passed to unstructured partition_pdf
        min_text_len - text elements smaller then this size will be dropped
        """
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.strategy = strategy
        self.languages = list(languages)
        self.min_text_len = min_text_len

    def _process_batch(self, X: Dict[str, PDFDoc]):
        parsed = {}
        scanned = {k: v for k, v in X.items() if v.metainfo.file_features.is_scanned}
        not_scanned = {k: v for k, v in X.items() if not v.metainfo.file_features.is_scanned}
        logger.warning(f"Processing {len(scanned)} scanned, {len(not_scanned)} native PDFs")
        # not scanned documents can be processed in parallel
        for batch_keys in split_every(not_scanned, self.batch_size):
            batch = {k: X[k] for k in batch_keys}
            p = self._process_batch_parallel(batch)
            parsed.update(p)
        print("finished parallel part")
        # but scanned ones only serially (it's already parallelized under the hood)

        p = self._process_serial(scanned)
        parsed.update(p)

        failed = {k: v for k, v in parsed.items() if isinstance(v, PDFError)}
        parsed = {k: v for k, v in parsed.items() if not isinstance(v, PDFError)}
        return parsed, failed

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        pdf = doc.metainfo.file_features.file
        if isinstance(pdf, str):
            input_kwargs = dict(filename=pdf)
        else:
            input_kwargs = dict(file=pdf)
        # if pdf is scanned use hi_res strategy, best so far
        input_kwargs["strategy"] = self.strategy
        if doc.metainfo.file_features.is_scanned:
            input_kwargs["strategy"] = "hi_res"
        # if pdf, extract text using partition_pdf
        # TODO: add support for other file types
        elements = partition_pdf(**input_kwargs, languages=self.languages)
        chunks = []
        for el in elements:
            if not isinstance(el, (doc_elements.NarrativeText, doc_elements.Text, doc_elements.Table)):
                continue

            if isinstance(el, doc_elements.Table):
                chunk_kwargs = dict(
                    non_embeddable_content=el.metadata.text_as_html, chunk_type=ChunkType.TABLE, locked=True
                )
                requires_fill = True  # mark it as requiring fill to generate it during postporcessing
            else:
                eldict = el.to_dict()
                text = eldict["text"]
                if len(text) < self.min_text_len:
                    continue
                chunk_kwargs = dict(text=text, chunk_type=ChunkType.TEXT, locked=False)
                requires_fill = False
            try:
                coords = eldict["metadata"]["coordinates"]
                norm_coords = [
                    (p[0] / coords["layout_width"], p[1] / coords["layout_height"]) for p in coords["points"]
                ]

                xmin, xmax, ymin, ymax = extract_bbox(norm_coords)
                chunk_kwargs["coordinates"] = [(xmin, ymin), (xmax, ymax)]
            except KeyError:
                coords = None

            try:
                chunk_kwargs["page"] = eldict["metadata"]["page_number"]
            except KeyError:
                chunk_kwargs["page"] = None

            chunk = PDFChunk(**chunk_kwargs)
            chunk.requires_fill = requires_fill
            chunks.append(chunk)
        doc.chunks = chunks
        return doc


class UnstructuredTextExtractorSerial(UnstructuredTextExtractor):
    parallel = None

    class UnstructuredGeneralExtractor(BaseProcessor):
        parallel = "process"
        operates_on = PDFDoc

        def __init__(
            self,
            languages=("eng",),
            min_text_len=20,
            batch_size=None,
            n_proc=None,
        ):
            """
            strategy, languages - passed to unstructured partition
            min_text_len - text elements smaller then this size will be dropped
            """
            super().__init__(n_proc=n_proc, batch_size=batch_size)
            self.languages = list(languages)
            self.min_text_len = min_text_len

        def _process_batch(self, X: Dict[str, PDFDoc]):
            parsed = {}
            for batch_keys in split_every(X, self.batch_size):
                batch = {k: X[k] for k in batch_keys}
                p = self._process_batch_parallel(batch)
                parsed.update(p)

            failed = {k: v for k, v in parsed.items() if isinstance(v, PDFError)}
            parsed = {k: v for k, v in parsed.items() if not isinstance(v, PDFError)}
            return parsed, failed

        # process general non-pdf files using unstructured partition
        def process_single(self, doc: PDFDoc) -> PDFDoc:
            pdf = doc.metainfo.file_features.file
            if isinstance(pdf, str):
                input_kwargs = dict(filename=pdf)
            else:
                input_kwargs = dict(file=pdf)

            elements = partition(**input_kwargs, languages=self.languages)
            chunks = []
            # collect all languages detected in the document, will assume most common is the document language
            languages = []
            # TODO: extract tables
            for el in elements:
                if not isinstance(el, (doc_elements.NarrativeText, doc_elements.Text, doc_elements.Table)):
                    continue
                eldict = el.to_dict()
                if isinstance(el, doc_elements.Table):
                    chunk_kwargs = dict(
                        non_embeddable_content=el.metadata.text_as_html, chunk_type=ChunkType.TABLE, locked=True
                    )
                    requires_fill = True  # mark it as requiring fill to generate it during postporcessing
                else:
                    chunk_kwargs = dict(text=eldict["text"], chunk_type=ChunkType.TEXT, locked=False)
                    requires_fill = False
                try:
                    page = eldict["metadata"]["page_number"]
                except KeyError:
                    page = None
                chunk = PDFChunk(page=page, coordinates=None, **chunk_kwargs)
                chunk.reliable = True
                chunk.requires_fill = requires_fill
                chunks.append(chunk)
                languages.append(detect_language(chunk.text))

            doc.metainfo.language = max(set(languages), key=languages.count)
            doc.chunks = chunks
            return doc
