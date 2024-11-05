import zipfile

from ..base import BaseProcessor
from ..datamodels import PDFDoc
from ..utils.xml_utils import clean_xml
from ..logging import logger


class OfficeMetaExtractor(BaseProcessor):
    """
    Extracts XML metadata from Microsoft Office formats and stores it as extra_metainfo.

    Methods:
        process_single(doc: PDFDoc) -> PDFDoc:
            Extracts XML metadata from the provided PDFDoc and stores it in the extra_metainfo attribute.
    """

    parallel = "thread"
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        try:
            zipf = zipfile.ZipFile(doc.metainfo.file_features.file, "r")
        except zipfile.BadZipFile:
            logger.error(f"Bad zip file: {doc.metainfo.file_features.file}")
            return doc
        xml_meta = []

        for file in zipf.namelist():
            if file.startswith("docProps") and file.endswith("xml"):
                xml_meta.append(clean_xml(zipf.read(file).decode()))

        doc.metainfo.extra_metainfo["office_metaifo"] = "\n".join(xml_meta)
        return doc
