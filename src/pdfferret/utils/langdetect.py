from typing import BinaryIO, Union
from lingua import Language, LanguageDetectorBuilder

from ..datamodels import MetaInfo, PDFDoc
from ..base import BaseProcessor

languages = [Language.ENGLISH, Language.GERMAN, Language.FRENCH]

lang_codes = [lang.iso_code_639_1.name.lower() for lang in languages]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

def detect_language(s: str):
    lang = detector.detect_language_of(s)
    return lang.iso_code_639_1.name.lower()

class LanguageDetector(BaseProcessor):
    parallel = False
    operates_on = MetaInfo

    def process_single(self, meta: MetaInfo) -> MetaInfo:
        if meta.abstract:
            lang = detector.detect_language_of(meta.abstract)
        elif meta.title:
            lang = detector.detect_language_of(meta.title)
        else: # if not known, assume it's english
            lang = Language.ENGLISH
        meta.language = lang.iso_code_639_1.name.lower()
        return meta

    