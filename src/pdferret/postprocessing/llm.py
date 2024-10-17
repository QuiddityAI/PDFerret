import logging

from llmonkey.llmonkey import LLMonkey
from pydantic import BaseModel

from ..base import BaseProcessor
from ..datamodels import ChunkType, PDFDoc

system_prompt_table = """You are a librarian, performing indexing of the library.
You will be provided with a table encoded as HTML. Write a very short summary
(no longer than 4 sentences) for it. Only include semantic information useful to find this table.
Return output as raw json without any extra characters, according to schema {"description": description you extracted}"""


class LLMTableResponse(BaseModel):
    description: str


system_prompt_summary = """You are a librarian, performing indexing of the library.
For every provided entry, you have different information available. Write a very short summary
(no longer than 4-5 sentences) for it. Only include semantic information useful to search this document.
If abstract is found in the information provided, return it instead of writing summary.
Do not include information about article structure, number of pages, etc.
Return output as raw json without any extra characters, according to schema {"summary": summary you extracted}"""


class LLMSummaryResponse(BaseModel):
    summary: str


class LLMPostprocessor(BaseProcessor):
    parallel = "thread"
    operates_on = PDFDoc

    def __init__(
        self,
        llm_table_description=True,
        llm_summary=False,
        llm_model="llama-3.2-3b-preview",
        llm_provider="groq",
        n_proc=None,
        batch_size=None,
        summary_max_chunks=5,
    ):
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.llm_table_description = llm_table_description
        self.llm_summary = llm_summary
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self.llmonkey = LLMonkey()
        self.summary_max_chunks = summary_max_chunks

    def process_single(self, pdfdoc: PDFDoc) -> PDFDoc:
        for chunk in pdfdoc.chunks:
            if self.llm_table_description and chunk.chunk_type == ChunkType.TABLE:
                try:
                    chunk.text = self._llm_table_descr(chunk.non_embeddable_content)
                except Exception as e:
                    logging.error(f"Failed to generate LLM table description: {e}")

        if self.llm_summary and not pdfdoc.metainfo.abstract:
            try:
                pdfdoc.metainfo.abstract = self._generate_llm_abstract(pdfdoc)
            except Exception as e:
                logging.error(f"Failed to generate LLM summary: {e}")
        return pdfdoc

    def _generate_llm_abstract(self, pdfdoc):
        useful_info = f"Filename: {pdfdoc.metainfo.file_features.filename}\n"

        if pdfdoc.metainfo.title:
            useful_info += f"Title: {pdfdoc.metainfo.title}\n"
        if pdfdoc.chunks:
            useful_info += "Content: "
            for idx, chunk in enumerate(pdfdoc.chunks):
                if idx >= self.summary_max_chunks:
                    break
                useful_info += chunk.text + "\n"

        summary_resp, raw_resp = self.llmonkey.generate_structured_response(
            provider=self.llm_provider,
            model_name=self.llm_model,
            data_model=LLMSummaryResponse,
            user_prompt=useful_info,
            system_prompt=system_prompt_summary,
            max_tokens=None,
            temperature=0.0,
        )
        if summary_resp:
            return summary_resp.summary
        else:
            raise ValueError("No summary was returned by LLM")

    def _llm_table_descr(self, table_as_html):
        descr_resp, raw_resp = self.llmonkey.generate_structured_response(
            self.llm_provider,
            self.llm_model,
            system_prompt=system_prompt_table,
            data_model=LLMTableResponse,
            user_prompt=table_as_html,
            temperature=0.0,
            max_tokens=None,
        )
        if descr_resp:
            return descr_resp.description
        else:
            raise ValueError("No table description was returned by LLM")

    def _llm_image_descr(self, image):
        # TODO: Implement image description
        raise NotImplementedError("Image description is not implemented yet")
