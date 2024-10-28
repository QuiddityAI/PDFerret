from lingua import Language, LanguageDetectorBuilder

from ..base import BaseProcessor
from ..datamodels import PDFDoc

languages = [Language.ENGLISH, Language.GERMAN, Language.FRENCH]

lang_codes = [lang.iso_code_639_1.name.lower() for lang in languages]
detector = LanguageDetectorBuilder.from_languages(*languages).build()


def detect_language(s: str):
    lang = detector.detect_language_of(s)
    if lang:
        return lang.iso_code_639_1.name.lower()
    else:  # if detection is unsuccessful, assume it's english
        return "en"


class LanguageDetector(BaseProcessor):
    """
    LanguageDetector is a processor that detects the language of a PDF document's metadata.

    Attributes:
        parallel (bool): Indicates whether the processor can run in parallel. Defaults to False.
        operates_on (type): Specifies the type of object the processor operates on. Defaults to PDFDoc.

    Methods:
        process_single(doc: PDFDoc) -> PDFDoc:
            Detects the language of the given PDF document's metadata. It first checks the abstract,
            then the title, and if neither is available, it defaults to English. The detected language
            is then set in the metadata.

            Args:
                doc (PDFDoc): The PDF document to process.

            Returns:
                PDFDoc: The processed PDF document with the detected language set in its metadata.
    """

    parallel = False
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        meta = doc.metainfo
        if meta.abstract:
            lang = detector.detect_language_of(meta.abstract)
        elif meta.title:
            lang = detector.detect_language_of(meta.title)
        else:  # if not known, assume it's english
            lang = Language.ENGLISH
        meta.language = lang.iso_code_639_1.name.lower()
        return doc
