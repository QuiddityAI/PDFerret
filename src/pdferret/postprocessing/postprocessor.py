from ..datamodels import PDFDoc
from ..thumbnails.thumbnailer import Thumbnailer
from .llm_postprocessor import LLMPostprocessor


class PostProcessor(object):
    def __init__(
        self,
        thumbnails=False,
        llm_table_description=False,
        llm_summary=False,
        llm_model="llama-3.2-3b-preview",
        llm_provider="groq",
        n_proc=None,
        batch_size=None,
    ):
        self.llm_table_description = llm_table_description
        self.llm_summary = llm_summary
        self.llm_model = llm_model
        self.llm_provider = llm_provider
        self.n_proc = n_proc
        self.batch_size = batch_size
        self.thumbnails = thumbnails

    def process_batch(self, pdfdocs: dict[str, PDFDoc]) -> dict[str, PDFDoc]:
        if self.llm_summary or self.llm_table_description:
            llm_processor = LLMPostprocessor(
                llm_table_description=self.llm_table_description,
                llm_summary=self.llm_summary,
                llm_model=self.llm_model,
                llm_provider=self.llm_provider,
                n_proc=self.n_proc,
                batch_size=self.batch_size,
            )
            pdfdocs, errors = llm_processor.process_batch(pdfdocs)
            if errors:
                raise Exception(f"Got error from LLMProcessor. This should not happen\n {errors}")
        if self.thumbnails:
            thumbnailer = Thumbnailer()
            pdfdocs = thumbnailer.process_batch(pdfdocs)
        return pdfdocs
