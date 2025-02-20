import dataclasses
import os

from llmonkey.llms import BaseLLMModel

from .base import BaseProcessor
from .converters.libreoffice import LibreOfficeConverter
from .metainfo.office_metaextractor import OfficeMetaExtractor
from .postprocessing.llm_postprocessor import LLMPostprocessor
from .text_extrators.pandoc_md import PandocMDExtractor
from .text_extrators.tika import TikaExtractor, TikaSpreadsheetExtractor
from .text_extrators.visual_extractor import VisualPDFExtractor
from .text_extrators.raw_text import RawTextExtractor
from .thumbnails.libreoffice import LibreOfficeThumbnailer
from .chunking import SimpleChunker


@dataclasses.dataclass
class PipelineStep:
    processor: BaseProcessor
    params: dict = dataclasses.field(default_factory=dict)

    def make_step(self):
        return self.processor(**self.params)


tika_url = os.getenv("PDFERRET_TIKA_SERVER_URL", "http://localhost:9998")
tika_ocr_strategy = os.getenv("PDFERRET_TIKA_OCR_STRATEGY", "NO_OCR")
visual_max_pages = int(os.getenv("PDFERRET_VISUAL_MAX_PAGES", 3))


def get_recipes(text_model: BaseLLMModel, vision_model: BaseLLMModel):
    recipes = {
        # docx and similar: 1) extract metadata from XML in the docx file,
        # 2) Get thumbnail using LibreOffice, 3) convert to markdown using pandoc, LLM postprocessing
        "docx": [
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(LibreOfficeThumbnailer),
            PipelineStep(PandocMDExtractor),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
            PipelineStep(SimpleChunker),
        ],
        "odt": [
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(LibreOfficeThumbnailer),
            PipelineStep(PandocMDExtractor),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
            PipelineStep(SimpleChunker),
        ],
        "txt": [
            PipelineStep(LibreOfficeThumbnailer),
            PipelineStep(RawTextExtractor),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
            PipelineStep(SimpleChunker),
        ],
        # doc: similar to docx but convert to docx before sending to pandoc
        # also doc is non-xml so we need to convert to docx before we can extract metadata
        "doc": [
            PipelineStep(LibreOfficeThumbnailer),
            PipelineStep(LibreOfficeConverter),
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(PandocMDExtractor),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
            PipelineStep(SimpleChunker),
        ],
        # pptx and similar: 0) Extract metainfo 1) convert to pdf, 2) extract text with Tika,
        # 3) extract additional info using visual model, 4) postprocess with LLM
        # visualpdfextractor also updates the thumbnail
        "ppt": [
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(LibreOfficeConverter, {"target_format": "pdf"}),
            PipelineStep(TikaExtractor, {"tika_url": tika_url}),
            PipelineStep(VisualPDFExtractor, {"model": vision_model, "max_pages": visual_max_pages}),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
            PipelineStep(SimpleChunker),
        ],
        "pptx": [
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(LibreOfficeConverter, {"target_format": "pdf"}),
            PipelineStep(TikaExtractor, {"tika_url": tika_url}),
            PipelineStep(VisualPDFExtractor, {"model": vision_model, "max_pages": visual_max_pages}),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
            PipelineStep(SimpleChunker),
        ],
        # pdf: 1) extract text with Tika + save metadata,
        # 2) extract additional info using visual model, 3) postprocess with LLM
        "pdf": [
            PipelineStep(
                TikaExtractor,
                {"tika_url": tika_url, "save_raw_metadata": True, "tika_ocr_strategy": tika_ocr_strategy},
            ),
            PipelineStep(VisualPDFExtractor, {"model": vision_model, "max_pages": visual_max_pages}),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
            PipelineStep(SimpleChunker),
        ],
        # xlsx and similar 1) extract metadata from XML in the xlsx file, 2) Get thumbnail using LibreOffice,
        # 3) extract text with Tika spreadsheet extractor (will convert spreadsheet to markdown),
        # 4) postprocess with LLM
        "xlsx": [
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(LibreOfficeThumbnailer),
            PipelineStep(TikaSpreadsheetExtractor, {"tika_url": tika_url}),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
        ],
        "xls": [
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(LibreOfficeThumbnailer),
            PipelineStep(TikaSpreadsheetExtractor, {"tika_url": tika_url}),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
        ],
        "ods": [
            PipelineStep(OfficeMetaExtractor),
            PipelineStep(LibreOfficeThumbnailer),
            PipelineStep(TikaSpreadsheetExtractor, {"tika_url": tika_url}),
            PipelineStep(LLMPostprocessor, {"llm_model": text_model}),
        ],
    }
    return recipes
