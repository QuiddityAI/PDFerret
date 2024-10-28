import io
import uuid

from ocrmypdf import ocr
from pypdf import PdfReader, PdfWriter

from .base import BaseProcessor
from .config import MAX_PAGES
from .datamodels import FileFeatures, MetaInfo, PDFDoc, PDFFile
from .logging import logger
from .utils.langdetect import detect_language
from .utils.scan_detector import is_scanned


class DummyFileInfoExtractor(BaseProcessor):
    parallel = "process"
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        fname = doc.metainfo.file_features.file if isinstance(doc.metainfo.file_features.file, str) else uuid.uuid4()
        doc.metainfo.file_features.filename = fname
        return doc


class FileInfoExtractor(BaseProcessor):
    parallel = "process"
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        fname = doc.metainfo.file_features.file if isinstance(doc.metainfo.file_features.file, str) else uuid.uuid4()
        reader = PdfReader(
            io.BytesIO(doc.metainfo.file_features.file)
            if isinstance(doc.metainfo.file_features.file, bytes)
            else doc.metainfo.file_features.file
        )
        is_scan = is_scanned(reader)
        text = "".join([reader.pages[i].extract_text() for i in range(min(3, len(reader.pages)))])
        if len(text) < 50:  # there might be some kind of noise but
            # 3 pages should definitely contain more than 50 chars
            logger.warning("PDF contains no text")
            if len(reader.pages) > MAX_PAGES:
                buff = io.BytesIO()
                writer = PdfWriter()
                for i in range(MAX_PAGES):
                    writer.add_page(reader.pages[i])
                writer.write(buff)
                buff.seek(0)
                doc.metainfo.file_features.file = buff

            out = io.BytesIO()
            ocr(input_file=doc.metainfo.file_features.file, output_file=out, force_ocr=True)
            reader = PdfReader(out)
            text = " ".join([reader.pages[i].extract_text() for i in range(min(3, len(reader.pages)))])
            doc.metainfo.file_features.file = out
        lang = detect_language(text)
        doc.metainfo.file_features.is_scanned = is_scan
        doc.metainfo.file_features.filename = fname
        doc.metainfo.language = lang
        doc.metainfo.npages = len(reader.pages)
        return doc
