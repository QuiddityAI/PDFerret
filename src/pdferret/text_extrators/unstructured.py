from typing import Dict

import numpy as np
from prometheus_client import Summary
from unstructured.documents import elements as doc_elements
from unstructured.partition.auto import partition
from unstructured.partition.pdf import partition_pdf

from ..base import BaseProcessor
from ..datamodels import MetaInfo, PDFChunk, PDFDoc, PDFError
from ..logging import logger
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
    operates_on = MetaInfo

    def __init__(self, strategy="auto", languages=("eng",), min_text_len=20, batch_size=None, n_proc=None):
        """
        strategy, languages - passed to unstructured partition_pdf
        min_text_len - text elements smaller then this size will be dropped
        """
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.strategy = strategy
        self.languages = list(languages)
        self.min_text_len = min_text_len

    # def _process_serial(self,
    #                     pdfs: Dict[str, Any]):
    #     parsed_batch = {}
    #     for _id, pdf in pdfs.items():
    #         ext = self._process_single(pdf)
    #         parsed_batch[_id] = ext

    #     return parsed_batch

    def _process_batch(self, X: Dict[str, MetaInfo]):
        parsed = {}
        scanned = {k: v for k, v in X.items() if v.file_features.is_scanned}
        not_scanned = {k: v for k, v in X.items() if not v.file_features.is_scanned}
        logger.warn(f"Processing {len(scanned)} scanned, {len(not_scanned)} native PDFs")
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

    def process_single(self, meta: MetaInfo) -> PDFDoc:
        pdf = meta.file_features.file
        if isinstance(pdf, str):
            input_kwargs = dict(filename=pdf)
        else:
            input_kwargs = dict(file=pdf)
        # if pdf is scanned use hi_res strategy, best so far
        input_kwargs["strategy"] = self.strategy
        if meta.file_features.is_scanned:
            input_kwargs["strategy"] = "hi_res"
        # if pdf, extract text using partition_pdf
        # TODO: add support for other file types
        elements = partition_pdf(**input_kwargs, languages=self.languages)
        chunks = []
        for el in elements:
            if not isinstance(el, (doc_elements.NarrativeText, doc_elements.Text)):
                continue

            eldict = el.to_dict()
            text = eldict["text"]
            if len(text) < self.min_text_len:
                continue

            coords = eldict["metadata"]["coordinates"]
            norm_coords = [(p[0] / coords["layout_width"], p[1] / coords["layout_height"]) for p in coords["points"]]

            xmin, xmax, ymin, ymax = extract_bbox(norm_coords)

            chunk = PDFChunk(
                page=eldict["metadata"]["page_number"], text=text, coordinates=[(xmin, ymin), (xmax, ymax)]
            )
            chunks.append(chunk)
        return PDFDoc(metainfo=meta, chunks=chunks)


class UnstructuredTextExtractorSerial(UnstructuredTextExtractor):
    parallel = None


class UnstructuredGeneralExtractor(BaseProcessor):
    parallel = "process"
    operates_on = MetaInfo

    def __init__(self, languages=("eng",), min_text_len=20, batch_size=None, n_proc=None):
        """
        strategy, languages - passed to unstructured partition_pdf
        min_text_len - text elements smaller then this size will be dropped
        """
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.languages = list(languages)
        self.min_text_len = min_text_len

    def _process_batch(self, X: Dict[str, MetaInfo]):
        parsed = {}
        for batch_keys in split_every(X, self.batch_size):
            batch = {k: X[k] for k in batch_keys}
            p = self._process_batch_parallel(batch)
            parsed.update(p)

        failed = {k: v for k, v in parsed.items() if isinstance(v, PDFError)}
        parsed = {k: v for k, v in parsed.items() if not isinstance(v, PDFError)}
        return parsed, failed

    # process general non-pdf files using unstructured partition
    def process_single(self, meta: MetaInfo) -> PDFDoc:
        pdf = meta.file_features.file
        if isinstance(pdf, str):
            input_kwargs = dict(filename=pdf)
        else:
            input_kwargs = dict(file=pdf)

        elements = partition(**input_kwargs, languages=self.languages)
        chunks = []
        # TODO: extract tables
        for el in elements:
            if not isinstance(el, (doc_elements.NarrativeText, doc_elements.Text)):
                continue

            eldict = el.to_dict()
            text = eldict["text"]
            if len(text) < self.min_text_len:
                continue
            try:
                page = eldict["metadata"]["page_number"]
            except KeyError:
                page = None
            chunk = PDFChunk(page=page, text=text, coordinates=None)
            chunks.append(chunk)
        return PDFDoc(metainfo=meta, chunks=chunks)
