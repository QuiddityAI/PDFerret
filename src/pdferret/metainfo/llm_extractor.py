import logging

from llmonkey.llmonkey import LLMonkey
from pydantic import BaseModel

from ..base import BaseProcessor
from ..datamodels import MetaInfo, PDFDoc

SYSTEM_PROMPT = """You are a librarian, performing indexing of the library.
For every provided entry, you have different information available. Write a very short summary
(no longer than 4 sentences) for it. Only include semantic information useful to search this document.
Do not include information about it's structure, number of pages, etc.
Return output as raw json without any extra characters, according to schema {"summary": summary you extracted}"""


class SummaryResponse(BaseModel):
    summary: str


class LLMMetaExtractor(BaseProcessor):
    parallel = "thread"
    operates_on = PDFDoc

    def __init__(self, model="llama-3.2-3b-preview", provider="groq", force_overwrite=False, max_chunks=5):
        super().__init__()
        self.provider = provider
        self.model = model
        self.llmonkey = LLMonkey()
        self.force_overwrite = force_overwrite
        self.max_chunks = max_chunks

    def process_single(self, pdfdoc: PDFDoc) -> PDFDoc:
        if (not pdfdoc.metainfo.abstract) or self.force_overwrite:
            try:
                pdfdoc.metainfo.abstract = self._generate_llm_abstract(pdfdoc)
            except Exception as e:
                logging.warning(e)
        return pdfdoc

    def _generate_llm_abstract(self, pdfdoc):
        useful_info = f"Filename: {pdfdoc.metainfo.file_features.filename}\n"

        if pdfdoc.metainfo.title:
            useful_info += f"Title: {pdfdoc.metainfo.title}\n"
        if pdfdoc.chunks:
            useful_info += "Content: "
            for idx, chunk in enumerate(pdfdoc.chunks):
                if idx >= self.max_chunks:
                    break
                useful_info += chunk.text + "\n"

        summary_resp, raw_resp = self.llmonkey.generate_structured_response(
            provider=self.provider,
            model_name=self.model,
            data_model=SummaryResponse,
            user_prompt=useful_info,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=None,
        )
        if summary_resp:
            return summary_resp.summary
        else:
            raise ValueError("No summary was returned by LLM")
