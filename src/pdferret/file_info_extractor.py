from typing import BinaryIO, Union
from pypdf import PdfReader
from ocrmypdf import ocr
import io
import uuid
from .base import BaseProcessor
from .datamodels import MetaInfo, FileFeatures, PDFFile
from .utils.scan_detector import is_scanned
from .utils.langdetect import detect_language
from .logging import logger


class FileInfoExtractor(BaseProcessor):
    parallel = "process"
    operates_on = PDFFile

    def process_single(self, pdf: PDFFile) -> MetaInfo:
        fname = pdf if isinstance(pdf, str) else uuid.uuid4()
        reader = PdfReader(pdf)
        is_scan = is_scanned(reader)
        text = reader.pages[0].extract_text()
        if not text:
            logger.warning("PDF contains no text")
            out = io.BytesIO()
            ocr(input_file=pdf, output_file=out, redo_ocr=True)
            reader = PdfReader(out)
            text = reader.pages[0].extract_text()
            pdf = out
        lang = detect_language(text)
        ffeatures = FileFeatures(file=pdf, is_scanned=is_scan, filename=fname)
        return MetaInfo(language=lang, file_features=ffeatures, npages=len(reader.pages))
