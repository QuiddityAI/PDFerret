from pypdf import PdfReader

from .base import BaseProcessor
from .datamodels import PDFDoc
from .utils.langdetect import detect_language
from .utils.scan_detector import is_scanned


class FileInfoExtractor(BaseProcessor):
    parallel = "process"
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        reader = PdfReader(doc.metainfo.file_features.file)
        is_scan = is_scanned(reader)
        text = reader.pages[0].extract_text()
        lang = detect_language(text)
        doc.metainfo.file_features.is_scanned = is_scan
        doc.metainfo.language = lang
        doc.metainfo.npages = len(reader.pages)
        return doc
