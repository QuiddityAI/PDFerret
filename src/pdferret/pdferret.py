import uuid
from typing import List

from .chunking import StandardChunker
from .datamodels import FileFeatures, MetaInfo, PDFDoc, PDFError, PDFFile
from .file_info_extractor import DummyFileInfoExtractor, FileInfoExtractor
from .metainfo.grobid_extractor import DummyMetaExtractor, GROBIDMetaExtractor
from .metainfo.llm_extractor import LLMMetaExtractor
from .text_extrators.grobid import GROBIDTextExtractor
from .text_extrators.unstructured import UnstructuredGeneralExtractor, UnstructuredTextExtractor
from .thumbnails.thumbnailer import Thumbnailer

meta_extractors = {"grobid": GROBIDMetaExtractor, "dummy": DummyMetaExtractor}
text_extractors = {"grobid": GROBIDTextExtractor, "unstructured": UnstructuredTextExtractor}
chunkers = {"standard": StandardChunker}


class PDFerret:
    def __init__(
        self,
        meta_extractor="grobid",
        text_extractor="grobid",
        chunker="standard",
        thumbnails=True,
        llm_summary=False,
        llm_table_description=False,
        llm_model="llama-3.2-3b-preview",
        llm_provider="groq",
    ):
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
        self.thumbnails = thumbnails
        if thumbnails:
            self.thumbnailer = Thumbnailer()

        self.llm_summary = llm_summary
        if llm_summary:
            self.llm_meta_extractor = LLMMetaExtractor()
        # TODO: implement table description extraction
        self.llm_table_description = llm_table_description
        self.llm_model = llm_model
        self.llm_provider = llm_provider

    def _sort_results(self, docs, failed_all, pdfs):
        # docs: extracted data, failed_all: dictionary containing all error messages
        # pdfs: original list of pdfs
        sorted_docs = [
            (
                docs[key]
                if key in docs
                else PDFDoc(
                    MetaInfo(file_features=FileFeatures(filename=pdfs[key] if isinstance(pdfs[key], str) else None))
                )
            )
            for key in pdfs
        ]
        sorted_failed = [failed_all[key] for key in pdfs if key in failed_all]
        return sorted_docs, sorted_failed

    def _is_pdf_file(self, file) -> bool:
        pdf_signature = b"%PDF-"
        if isinstance(file, str):
            try:
                with open(file, "rb") as f:
                    file_start = f.read(5)
            except IOError:
                return False
        elif isinstance(file, bytes):
            file_start = file[:5]
        elif hasattr(file, "read"):
            file_start = file.read(5)
            file.seek(0)  # Reset the file pointer to the beginning
        else:
            return False
        return file_start.startswith(pdf_signature)

    def _postprocess(self, docs: List[PDFDoc]) -> List[PDFDoc]:
        if self.thumbnails:
            # thumbnailer never returns errors, instead it fails silently
            # and sets thumbnail to None if it fails
            docs, failed = self.thumbnailer.process_batch(docs)
        if self.llm_summary:
            docs, failed = self.llm_meta_extractor.process_batch(docs)
        return docs

    def extract_batch(self, files: List[PDFFile]) -> tuple[List[PDFDoc], List[PDFError]]:
        failed_all = {}
        # assign unique ids to every item
        if isinstance(files[0], str):
            files = {v: v for v in files}
        elif isinstance(files[0], bytes):
            files = {uuid.uuid4(): v for v in files}
        # use duck typing to detect if file is file-like object
        # assign UUID as identifier instead of filename
        # and load to memory if as file-like objects can't be shared
        # between processes when multiprocessing is used
        # TODO: check file size
        elif "read" in dir(files[0]):
            files = {uuid.uuid4(): v for v in files}

        else:
            ValueError("Argument to extract_batch must be a list of file paths or file-like objects")

        # separate pdfs from other files
        pdfs = {k: v for k, v in files.items() if self._is_pdf_file(v)}
        other_files = {k: v for k, v in files.items() if k not in pdfs}

        # firstly, heuristically detect if pdf is scanned and its language:
        metainfo, failed = self.fileinfoextractor.process_batch(pdfs)
        failed_all.update(failed)

        # if grobid is used for both text and meta extraction run it just once
        if isinstance(self.meta_extractor, meta_extractors["grobid"]) and isinstance(
            self.text_extractor, text_extractors["grobid"]
        ):
            self.text_extractor.extract_meta = True
            docs, failed = self.text_extractor.process_batch(metainfo)
            failed_all.update(failed)
            if other_files:
                self._process_nonpdf_files(failed_all, other_files, docs)
            if self.chunker:
                docs, failed = self.chunker.process_batch(docs)
                failed_all.update(failed)

            docs = self._postprocess(docs)
            return self._sort_results(docs, failed_all, files)

        # otherwise extract meta and text separately then combine
        # note that metaextractors update the metainfo, while
        # doc extractors convert it to PDFDoc combining metainfo with chunks
        metainfo, failed = self.meta_extractor.process_batch(metainfo)
        failed_all.update(failed)
        docs, failed = self.text_extractor.process_batch(metainfo)
        failed_all.update(failed)
        # finally extract non-pdf files
        if other_files:
            self._process_nonpdf_files(failed_all, other_files, docs)

        if self.chunker:
            docs, failed = self.chunker.process_batch(docs)
            failed_all.update(failed)
        docs = self._postprocess(docs)
        return self._sort_results(docs, failed_all, files)

    def _process_nonpdf_files(self, failed_all, other_files, docs):
        """
        Small subprogramm to process non-PDF files by extracting metadata and updating the provided document collections.

        Args:
            failed_all (dict): A dict to store the filenames of files that failed processing.
            other_files (list): A list of non-PDF files to be processed.
            docs (dict): A dictionary to store the successfully processed document metadata.

        This method uses two extractors:
        - DummyFileInfoExtractor: Extracts basic metadata from the non-PDF files.
        - UnstructuredGeneralExtractor: Processes the extracted metadata to generate document information.

        The method updates the `failed_all` dict with any files that fail during either extraction step,
        and updates the `docs` dictionary with the successfully processed document metadata.
        """
        dummy_extractor = DummyFileInfoExtractor()
        other_metainfo, failed = dummy_extractor.process_batch(other_files)
        failed_all.update(failed)
        general_extractor = UnstructuredGeneralExtractor()
        nonpdf_docs, failed = general_extractor.process_batch(other_metainfo)
        docs.update(nonpdf_docs)
        failed_all.update(failed)
