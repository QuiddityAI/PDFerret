from typing import BinaryIO, Union
from pypdf import PdfReader, PdfWriter
from ocrmypdf import ocr
import io
import uuid
from .base import BaseProcessor
from .datamodels import MetaInfo, FileFeatures, PDFFile
from .utils.scan_detector import is_scanned
from .utils.langdetect import detect_language
from .logging import logger
from .config import MAX_PAGES


class FileInfoExtractor(BaseProcessor):
    parallel = "process"
    operates_on = PDFFile

    def process_single(self, pdf: PDFFile) -> MetaInfo:
        fname = pdf if isinstance(pdf, str) else uuid.uuid4()
        reader = PdfReader(pdf)
        is_scan = is_scanned(reader)
        text = "".join([reader.pages[i].extract_text()
                        for i in range(min(3, len(reader.pages)))])
        if len(text) < 50:  # there might be some kind of noise but 
                            # 3 pages should definitely contain more then 50 chars
            logger.warning("PDF contains no text")
            if len(reader.pages) > MAX_PAGES:
                buff = io.BytesIO()
                writer = PdfWriter()
                for i in range(MAX_PAGES):
                    writer.add_page(reader.pages[i])
                writer.write(buff)
                buff.seek(0)
                pdf = buff

            out = io.BytesIO()
            ocr(input_file=pdf, output_file=out, force_ocr=True)
            reader = PdfReader(out)
            text = " ".join([reader.pages[i].extract_text()
                             for i in range(min(3, len(reader.pages)))])
            pdf = out
        lang = detect_language(text)
        ffeatures = FileFeatures(file=pdf, is_scanned=is_scan, filename=fname)
        return MetaInfo(language=lang, file_features=ffeatures, npages=len(reader.pages))
