import glob
import uuid
from typing import BinaryIO, Dict, List, Union

from .chunking import StandardChunker
from .datamodels import MetaInfo, PDFDoc, PDFFile
from .file_info_extractor import FileInfoExtractor
from .metainfo_extractor import GROBIDMetaExtractor
from .text_extrators.grobid import GROBIDTextExtractor
from .text_extrators.unstructured import UnstructuredTextExtractor

meta_extractors = {"grobid": GROBIDMetaExtractor}
text_extractors = {"grobid": GROBIDTextExtractor,
                   "unstructured": UnstructuredTextExtractor}
chunkers = {"standard": StandardChunker}


class PDFerret():
    def __init__(self, meta_extractor="grobid", text_extractor="grobid", chunker="standard"):
        """Main class to run PDF data extraction

        for now only text_extractor supports two options, either "grobid" or "unstructured", 
        rest is reseved for the future

        TODO: Implement detection of bad OCR quality and automatic re-OCR
        TODO: (maybe) use OpenAI API to detect bad OCR / post-improve OCR quality
        TODO: Limit max pages to process
        TODO: position-aware chunk combining
        TODO: allow running different text extractor if necessary (e.g. hi_res unstructured for PDF without text)


        Args:
            meta_extractor (str or Extractor instance): class performing metadata extraction. Defaults to "grobid".
            text_extractor (str or Extractor instance): class performing text body extraction. Defaults to "grobid".
            chunker (str or Processor instance): class performing chunking. Defaults to "standard".
        """
        if isinstance(meta_extractor, str):
            self.meta_extractor = meta_extractors[meta_extractor]()
        else:
            self.meta_extractor = meta_extractor
        if isinstance(text_extractor, str):
            self.text_extractor = text_extractors[text_extractor]()
        else:
            self.text_extractor = text_extractor
        if isinstance(chunker, str):
            self.chunker = chunkers[chunker]()
        else:
            self.chunker = chunker

        self.fileinfoextractor = FileInfoExtractor()

    def extract_batch(self, pdfs: List[PDFFile]) -> List[PDFDoc]:
        # assign unique ids to every item
        if isinstance(pdfs[0], str):
            pdfs = {v: v for v in pdfs}

        elif isinstance(pdfs[0], BinaryIO):
            pdfs = {uuid.uuid4(): v for v in pdfs}

        else:
            ValueError(
                "Argument to extract_batch must be a list of file paths of BinaryIO objects")

        # firstly, heuristically detect if pdf is scanned and its language:
        metainfo = self.fileinfoextractor.process_batch(pdfs)

        # if grobid is used for both text and meta extraction run it just once
        if (isinstance(self.meta_extractor, meta_extractors['grobid']) and
                isinstance(self.text_extractor, text_extractors['grobid'])):
            self.text_extractor.extract_meta = True
            docs = self.text_extractor.process_batch(metainfo)
            if self.chunker:
                docs = self.chunker.process_batch(docs)
            sorted_docs = [docs[key] if key in docs else PDFDoc()
                           for key in pdfs]
            return sorted_docs
        # otherwise extract meta and text separately then combine
        # note that metaextractors update the metainfo, while
        # doc extractors convert it to PDFDoc combining metainfo with chunks
        metainfo = self.meta_extractor.process_batch(metainfo)
        docs = self.text_extractor.process_batch(metainfo)
        if self.chunker:
            docs = self.chunker.process_batch(docs)

        sorted_docs = [docs[key] if key in docs else PDFDoc() for key in pdfs]
        return sorted_docs
