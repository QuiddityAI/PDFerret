import os
import tempfile
from typing import Dict

import pypdfium2 as pdfium

from ..base import BaseProcessor
from ..datamodels import MetaInfo, PDFDoc, PDFError


def make_thumnail_pdfium(file: str, output_dir: str):
    pdf = pdfium.PdfDocument(file)
    first_page = pdf[0]
    image = first_page.render(scale=1).to_pil()
    base_fname = os.path.basename(file)
    base_fname, _ = os.path.splitext(base_fname)
    thumbnail_path = os.path.join(output_dir, f"{base_fname}.png")
    image.save(thumbnail_path, "PNG")


class PDFiumThumbnailer(BaseProcessor):
    parallel = "process"
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        # just dummy, actual processing is in _process_batch
        return doc

    def _process_batch(self, X: Dict[str, PDFDoc]) -> tuple[Dict[str, PDFDoc], Dict[str, PDFError]]:
        with tempfile.TemporaryDirectory() as output_dir:
            for doc in X.values():
                meta = doc.metainfo
                make_thumnail_pdfium(meta.file_features.file, output_dir)
                base_name = os.path.basename(meta.file_features.file)
                name, _ = os.path.splitext(base_name)
                thumbnail_path = os.path.join(output_dir, f"{name}.png")
                try:
                    with open(thumbnail_path, "rb") as f:
                        meta.thumbnail = f.read()
                except FileNotFoundError:
                    pass
        return X, {}
