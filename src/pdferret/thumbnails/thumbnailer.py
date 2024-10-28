from typing import Dict

from ..datamodels import MetaInfo, PDFError
from .libreoffice import LibreOfficeThumbnailer
from .pdf import PDF2ImageThumbnailer

extension_map = {
    "docx": LibreOfficeThumbnailer,
    "doc": LibreOfficeThumbnailer,
    "xls": LibreOfficeThumbnailer,
    "xlsx": LibreOfficeThumbnailer,
    "ppt": LibreOfficeThumbnailer,
    "pptx": LibreOfficeThumbnailer,
    "pdf": PDF2ImageThumbnailer,
    "other": LibreOfficeThumbnailer,
}


class Thumbnailer:
    def __init__(self) -> None:
        pass

    def process_batch(self, X: Dict[str, MetaInfo]) -> Dict[str, MetaInfo]:
        # get the extension of the file
        # group files by extension, prepare batch for each extension
        # use corresponding thumbnailer for each batch
        # merge the results
        # return the merged results
        for ext, thumbnailer in extension_map.items():
            if ext == "other":
                batch = {k: v for k, v in X.items() if k.split(".")[-1] not in extension_map}
            else:
                batch = {k: v for k, v in X.items() if k.endswith(ext)}
            if batch:
                thumbnailer_instance = thumbnailer()
                processed_batch, errors = thumbnailer_instance.process_batch(batch)
                for k, v in processed_batch.items():
                    X[k] = v
        return X
