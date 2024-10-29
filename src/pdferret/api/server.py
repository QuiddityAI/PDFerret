import base64
import json
import tempfile
from typing import Annotated, Any, List, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from ..datamodels import ChunkType, FileFeatures, MetaInfo, PDFChunk, PDFDoc, PDFError
from ..pdferret import PDFerret

app = FastAPI()

PydanticPDFDoc = pydantic_dataclass(PDFDoc, config=ConfigDict(arbitrary_types_allowed=True))
PydanticPDFError = pydantic_dataclass(PDFError)


class PerFileSettings(BaseModel):
    lang: Literal["", "en", "de"] = ""
    extra_metainfo: dict[str, str] = {}


class PDFerretParams(BaseModel):
    vision_model: str = "Mistral_Pixtral"
    text_model: str = "Nebius_Llama_3_1_70B_fast"
    lang: Literal["en", "de"] = "en"
    return_images: bool = True
    perfile_settings: dict[str, PerFileSettings] = {}

    # necessary to convert string to Pydantic model on-the-fly
    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class PDFerretResults(BaseModel):
    extracted: List[PydanticPDFDoc]
    errors: List[PydanticPDFError]


def _prepare_metainfo(metainfo: MetaInfo, return_images: bool = False) -> MetaInfo:
    metainfo.file_features.file = None
    # clean up extra metainfo which was only used
    # to generate AI metainfo
    metainfo.extra_metainfo = None
    if metainfo.thumbnail and return_images:
        metainfo.thumbnail = base64.b64encode(metainfo.thumbnail).decode("utf-8")
    else:
        metainfo.thumbnail = None
    return metainfo


def _prepare_chunks(chunks: List[PDFChunk], return_images: bool = False) -> List[PDFChunk]:
    for chunk in chunks:
        if chunk.chunk_type in {ChunkType.FIGURE, ChunkType.VISUAL_PAGE} and chunk.non_embeddable_content:
            if return_images:
                chunk.non_embeddable_content = base64.b64encode(chunk.non_embeddable_content).decode("utf-8")
            else:
                chunk.non_embeddable_content = None
    return chunks


# # This endpoint is not used in the final version
# @app.post("/process_files_by_path")
# def process_files_by_path(pdfs: List[str], params: PDFerretParams) -> PDFerretResults:
#     extractor = PDFerret(**params.model_dump())
#     extracted, errors = extractor.extract_batch(pdfs)
#     return PDFerretResults(
#         extracted=[PydanticPDFDoc(metainfo=e.metainfo, chunks=e.chunks) for e in extracted],
#         errors=[PydanticPDFError(exc=e.exc, traceback="\n".join(e.traceback), file=str(e.file)) for e in errors],
#     )


@app.post("/process_files_by_stream")
def process_files_by_stream(
    pdfs: Annotated[List[UploadFile], File()], params: Annotated[PDFerretParams, Form()]
) -> PDFerretResults:

    filanames = [f.filename for f in pdfs]
    if len(set(filanames)) != len(filanames):
        raise HTTPException(status_code=400, detail="Filenames must be unique")

    extractor = PDFerret(**params.model_dump())
    perfile_settings = params.perfile_settings
    for key in perfile_settings:
        if key not in filanames:
            raise HTTPException(status_code=400, detail=f"File {key} has settings, but is not found")

    # load actual file content from stream and save to temporary directory
    # handling files as stream is not parallelizable
    pdfdocs = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for pdf in pdfs:
            with open(f"{tmpdir}/{pdf.filename}", "wb") as f:
                f.write(pdf.file.read())
            # create PDFDoc objects for each file
            ffeatures = FileFeatures(filename=pdf.filename, file=f"{tmpdir}/{pdf.filename}")
            # get perfile settings if available
            lang = perfile_settings.get(pdf.filename, PerFileSettings()).lang or params.lang
            extra_metainfo = perfile_settings.get(pdf.filename, PerFileSettings()).extra_metainfo

            meta = MetaInfo(file_features=ffeatures, language=lang, extra_metainfo=extra_metainfo)
            doc = PDFDoc(metainfo=meta, chunks=[])
            pdfdocs.append(doc)
        # params.lang is a default language for all files unless specified in perfile_settings
        extracted, errors = extractor.extract_batch(pdfdocs=pdfdocs, lang=params.lang)

    # prepare results, remove extra metainfo and convert images to base64
    # controlled by return_images parameter
    kwds = {"return_images": params.return_images}
    return PDFerretResults(
        extracted=[
            PydanticPDFDoc(metainfo=_prepare_metainfo(e.metainfo, **kwds), chunks=_prepare_chunks(e.chunks, **kwds))
            for e in extracted
        ],
        errors=[PydanticPDFError(exc=e.exc, traceback="\n".join(e.traceback), file=str(e.file)) for e in errors],
    )
