import io
from typing import List

from llmonkey.llms import BaseLLMModel
from pdf2image import convert_from_path

from ..base import BaseProcessor
from ..datamodels import ChunkType, PDFChunk, PDFDoc


def convert_pdf_to_jpg(file: str, max_pages: int = 3) -> List[bytes]:
    pages_as_pil = convert_from_path(file, first_page=0, last_page=max_pages, dpi=100)
    images = []
    for pil_page in pages_as_pil:
        buff = io.BytesIO()
        pil_page.save(buff, "JPEG")
        raw_bytes = buff.getvalue()
        images.append(raw_bytes)
        buff.close()
    return images


# this didn't really work, probably would require a separate call to the model to make it reliable
#    Add word "handwritten" or "hand-drawn" if the document is handwritten or hand-drawn.""",

prompt = {
    "en": "You will receive a page of the document. Summarize the content in several sentences (no more than 250 words).",
    "de": "Sie erhalten eine Seite des Dokuments. Fassen Sie den Inhalt in mehreren Sätzen zusammen (nicht mehr als 250 Wörter).",
}


class VisualPDFExtractor(BaseProcessor):
    parallel = "thread"
    operates_on = PDFDoc

    def __init__(
        self, model: BaseLLMModel, max_pages: int = 3, update_thumbnail: bool = True, batch_size=None, n_proc=None
    ):
        super().__init__(batch_size=batch_size, n_proc=n_proc)
        self.model = model
        self.max_pages = max_pages
        self.update_thumbnail = update_thumbnail

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        imgs = convert_pdf_to_jpg(doc.metainfo.file_features.file, self.max_pages)
        if self.update_thumbnail:
            doc.metainfo.thumbnail = imgs[0]
        lang = doc.metainfo.language or "en"
        if lang not in prompt:
            lang = "en"

        for img in imgs:
            resp = self.model.generate_prompt_response(user_prompt=prompt[lang], image=img, temperature=0.2, max_tokens=1000)
            if not resp:
                continue
            chunk = PDFChunk(
                text=resp.conversation[-1].content, non_embeddable_content=img, chunk_type=ChunkType.VISUAL_PAGE
            )
            doc.chunks.append(chunk)
        return doc
