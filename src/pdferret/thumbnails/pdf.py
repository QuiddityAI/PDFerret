import io
from typing import Dict, List

from pdf2image import convert_from_path

from ..base import BaseProcessor
from ..datamodels import PDFDoc, PDFError


def convert_pdf_to_jpg(file: str) -> List[bytes]:
    pages_as_pil = convert_from_path(file, first_page=0, last_page=1, dpi=100)
    pil_page = pages_as_pil[0]
    buff = io.BytesIO()
    pil_page.save(buff, "JPEG")
    raw_bytes = buff.getvalue()
    buff.close()
    return raw_bytes


class PDF2ImageThumbnailer(BaseProcessor):
    parallel = "thread"
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        # just dummy, actual processing is in _process_batch
        return doc

    def _process_batch(self, X: Dict[str, PDFDoc]) -> tuple[Dict[str, PDFDoc], Dict[str, PDFError]]:
        for doc in X.values():
            meta = doc.metainfo
            thumbnail = convert_pdf_to_jpg(meta.file_features.file)
            doc.metainfo.thumbnail = thumbnail

        return X, {}
