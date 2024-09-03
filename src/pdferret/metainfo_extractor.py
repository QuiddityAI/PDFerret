import io
import os

from pypdf import PdfReader, PdfWriter

from . import scipdf
from .base import BaseProcessor
from .config import GROBID_URL
from .datamodels import MetaInfo


class GROBIDMetaExtractor(BaseProcessor):
    parallel = "thread"
    operates_on = MetaInfo

    def __init__(self, grobid_url=None, batch_size=None, n_proc=None):
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        if grobid_url:
            self.grobid_url = grobid_url
        else:
            self.grobid_url = GROBID_URL

    def process_single(self, meta: MetaInfo) -> MetaInfo:
        reader = PdfReader(meta.file_features.file)
        buff = io.BytesIO()
        writer = PdfWriter()
        # extracting first 2 pages of PDF, assuming it contains all relevant metainfo
        _ = writer.add_page(reader.pages[0])
        _ = writer.add_page(reader.pages[1])
        writer.write(buff)
        parsed = scipdf.parse_pdf_to_dict(buff.getvalue(), grobid_url=self.grobid_url)
        target_keys = ["title", "authors", "pub_date", "abstract"]
        for k in target_keys:
            setattr(meta, k, parsed[k])
        # Maybe TODO: check if abstract is always correstly returned,
        # maybe take first block of the text if it's empty
        return meta
