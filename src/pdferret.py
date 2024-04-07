from .metainfo_extractor import GROBIDMetaExtractor
from .text_extrators.unstructured import UnstructuredTextExtractor
from .text_extrators.grobid import GROBIDTextExtractor
from typing import BinaryIO, Dict, Union
from .datamodels import PDFDoc, MetaInfo
from .chunking import StandardChunker
from .scan_detector import is_scanned

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
        TODO: Handle non-English documents
        TODO: Handle long texts (like theses)

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

    def extract_batch(self, pdfs: Dict[str, Union[str, BinaryIO]]) -> Dict[str, PDFDoc]:
        # firstly, heuristically detect if pdf is scanned

        # if grobid is used for both text and meta extraction run it just once
        if (isinstance(self.meta_extractor, meta_extractors['grobid']) and
                isinstance(self.text_extractor, text_extractors['grobid'])):
            self.text_extractor.extract_meta = True
            docs = self.text_extractor.extract_batch(pdfs)
            if self.chunker:
                docs = self.chunker.process_batch(docs)
            return docs
        # otherwise extract meta and text separately then combine
        metainfo = self.meta_extractor.extract_batch(pdfs)
        chunks = self.text_extractor.extract_batch(pdfs)
        extracted_pdf_docs = {}
        for key in pdfs:
            article_meta = metainfo[key] if key in metainfo else MetaInfo()
            article_chunks = chunks[key] if key in chunks else []
            extracted_pdf_docs[key] = PDFDoc(article_meta, article_chunks)

        if self.chunker:
            extracted_pdf_docs = self.chunker.process_batch(extracted_pdf_docs)
        return extracted_pdf_docs
