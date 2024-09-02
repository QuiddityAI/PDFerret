import glob
import uuid
from typing import BinaryIO, Dict, List, Union

from .chunking import StandardChunker
from .datamodels import MetaInfo, PDFDoc, PDFFile, FileFeatures, PDFError
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

    def _sort_results(self, docs, failed_all, pdfs):
        # docs: extracted data, failed_all: dictionary containing all error messages
        # pdfs: original list of pdfs
        sorted_docs = [docs[key] if key in docs
                       else PDFDoc(MetaInfo(file_features=FileFeatures(filename=pdfs[key] 
                                                  if isinstance(pdfs[key], str) else None)))
                       for key in pdfs]
        sorted_failed = [failed_all[key] for key in pdfs if key in failed_all]
        return sorted_docs, sorted_failed

    def extract_batch(self, pdfs: List[PDFFile]) -> tuple[List[PDFDoc], List[PDFError]]:
        failed_all = {}
        # assign unique ids to every item
        if isinstance(pdfs[0], str):
            pdfs = {v: v for v in pdfs}
        elif isinstance(pdfs[0], bytes):
            pdfs = {uuid.uuid4(): v for v in pdfs}
        # use duck typing to detect if pdf is file-like object
        # assign UUID as identifier instead of filename
        # and load to memory if as file-like objects can't be shared
        # between processes when multiprocessing is used
        # TODO: chech file size
        elif "read" in dir(pdfs[0]):
            pdfs = {uuid.uuid4(): v.read() for v in pdfs}

        else:
            ValueError(
                "Argument to extract_batch must be a list of file paths of file-like objects")

        # firstly, heuristically detect if pdf is scanned and its language:
        metainfo, failed = self.fileinfoextractor.process_batch(pdfs)
        failed_all.update(failed)

        # if grobid is used for both text and meta extraction run it just once
        if (isinstance(self.meta_extractor, meta_extractors['grobid']) and
                isinstance(self.text_extractor, text_extractors['grobid'])):
            self.text_extractor.extract_meta = True
            docs, failed = self.text_extractor.process_batch(metainfo)
            failed_all.update(failed)

            if self.chunker:
                docs, failed = self.chunker.process_batch(docs)
                failed_all.update(failed)

            return self._sort_results(docs, failed_all, pdfs)

        # otherwise extract meta and text separately then combine
        # note that metaextractors update the metainfo, while
        # doc extractors convert it to PDFDoc combining metainfo with chunks
        metainfo, failed = self.meta_extractor.process_batch(metainfo)
        failed_all.update(failed)
        docs, failed = self.text_extractor.process_batch(metainfo)
        failed_all.update(failed)
        if self.chunker:
            docs, failed = self.chunker.process_batch(docs)
            failed_all.update(failed)

        return self._sort_results(docs, failed_all, pdfs)
