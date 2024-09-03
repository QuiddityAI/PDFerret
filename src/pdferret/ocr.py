from pypdf import PdfReader

from .base import BaseProcessor
from .datamodels import FileFeatures, MetaInfo, PDFFile
from .utils.langdetect import detect_language
from .utils.scan_detector import is_scanned


class FileInfoExtractor(BaseProcessor):
    parallel = "process"
    operates_on = PDFFile

    def process_single(self, pdf: PDFFile) -> MetaInfo:
        reader = PdfReader(pdf)
        is_scan = is_scanned(reader)
        text = reader.pages[0].extract_text()
        lang = detect_language(text)
        ffeatures = FileFeatures(file=pdf, is_scanned=is_scan)
        return MetaInfo(language=lang, file_features=ffeatures, npages=len(reader.pages))
