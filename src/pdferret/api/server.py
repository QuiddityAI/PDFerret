import base64
import json
import tempfile
import uuid
from typing import Annotated, Any, List, Literal, Union

from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from ..datamodels import ChunkType, MetaInfo, PDFChunk, PDFDoc, PDFError
from ..pdferret import PDFerret

app = FastAPI()

PydanticPDFDoc = pydantic_dataclass(PDFDoc, config=ConfigDict(arbitrary_types_allowed=True))
PydanticPDFError = pydantic_dataclass(PDFError)


class PDFerretParams(BaseModel):
    vision_model: str = "Mistral_Pixtral"
    text_model: str = "Nebius_Llama_3_1_70B_fast"
    lang: Literal["en", "de"] = "en"
    return_images: bool = True

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


@app.post("/process_files_by_path")
def process_files_by_path(pdfs: List[str], params: PDFerretParams) -> PDFerretResults:
    extractor = PDFerret(**params.model_dump())
    extracted, errors = extractor.extract_batch(pdfs)
    return PDFerretResults(
        extracted=[PydanticPDFDoc(metainfo=e.metainfo, chunks=e.chunks) for e in extracted],
        errors=[PydanticPDFError(exc=e.exc, traceback="\n".join(e.traceback), file=str(e.file)) for e in errors],
    )


@app.post("/process_files_by_stream")
def process_files_by_stream(
    pdfs: Annotated[List[UploadFile], File()], params: Annotated[PDFerretParams, Form()]
) -> PDFerretResults:

    extractor = PDFerret(**params.model_dump())

    # load actual file content from stream and save to temporary directory
    # handling files as stream is not parallelizable
    with tempfile.TemporaryDirectory() as tmpdir:
        for pdf in pdfs:
            pdf.filename = uuid.uuid4().hex + pdf.filename
            with open(f"{tmpdir}/{pdf.filename}", "wb") as f:
                f.write(pdf.file.read())
        extracted, errors = extractor.extract_batch([f"{tmpdir}/{pdf.filename}" for pdf in pdfs], lang=params.lang)

    # restore original filename
    for e in extracted:
        original_filename = e.metainfo.file_features.filename.split("/")[-1]
        e.metainfo.file_features.filename = original_filename[32:]  # 32 is length of uuid

    kwds = {"return_images": params.return_images}
    return PDFerretResults(
        extracted=[
            PydanticPDFDoc(metainfo=_prepare_metainfo(e.metainfo, **kwds), chunks=_prepare_chunks(e.chunks, **kwds))
            for e in extracted
        ],
        errors=[PydanticPDFError(exc=e.exc, traceback="\n".join(e.traceback), file=str(e.file)) for e in errors],
    )
