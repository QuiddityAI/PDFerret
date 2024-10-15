import logging
from typing import Dict

import numpy as np
from llmonkey.llmonkey import LLMonkey
from prometheus_client import Summary
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


class LLMTableResponse(BaseModel):
    description: str


SYSTEM_PROMPT = """You are a librarian, performing indexing of the library.
You will be provided with a table encoded as HTML. Write a very short summary
(no longer than 4 sentences) for it. Only include semantic information useful to find this table.
Return output as raw json without any extra characters, according to schema {"description": description you extracted}"""


class UnstructuredGeneralExtractor(BaseProcessor):
    parallel = "process"
    operates_on = MetaInfo

    def __init__(
        self,
        languages=("eng",),
        min_text_len=20,
        batch_size=None,
        n_proc=None,
        llm_table_description=True,
        llm_model="llama-3.2-3b-preview",
        llm_provider="groq",
    ):
        """
        strategy, languages - passed to unstructured partition_pdf
        min_text_len - text elements smaller then this size will be dropped
        """
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.languages = list(languages)
        self.min_text_len = min_text_len
        self.llm_table_description = llm_table_description
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self.llmonkey = LLMonkey()

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
        # collect all languages detected in the document, will assume most common is the document language
        languages = []
        # TODO: extract tables
        for el in elements:
            if not isinstance(el, (doc_elements.NarrativeText, doc_elements.Text, doc_elements.Table)):
                continue
            eldict = el.to_dict()
            if isinstance(el, doc_elements.Table):
                chunk_kwargs = self._handle_table(el)
                chunk_kwargs["chunk_type"] = ChunkType.TABLE
                chunk_kwargs["locked"] = True
            else:
                chunk_kwargs = dict(text=eldict["text"], chunk_type=ChunkType.TEXT, locked=False)
            try:
                page = eldict["metadata"]["page_number"]
            except KeyError:
                page = None
            chunk = PDFChunk(page=page, coordinates=None, **chunk_kwargs)
            chunk.reliable = True
            chunks.append(chunk)
            languages.append(detect_language(chunk_kwargs["text"]))

        meta.language = max(set(languages), key=languages.count)
        return PDFDoc(metainfo=meta, chunks=chunks)

    def _handle_table(self, el: doc_elements.Table):
        table_as_html = el.metadata.text_as_html
        if self.llm_table_description:
            text = self._llm_table_summary(table_as_html)
            return dict(text=text, non_embeddable_content=table_as_html)
        else:
            return dict(non_embeddable_content=table_as_html)

    def _llm_table_summary(self, table_as_html):
        descr_resp, raw_resp = self.llmonkey.generate_structured_response(
            self.llm_provider,
            self.llm_model,
            system_prompt=SYSTEM_PROMPT,
            data_model=LLMTableResponse,
            user_prompt=table_as_html,
            temperature=0.0,
            max_tokens=None,
        )
        if descr_resp:
            return descr_resp.description
        else:
            logging.warning("No table description was returned by LLM")
            return ""
