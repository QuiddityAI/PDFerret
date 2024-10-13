import base64
import json
import tempfile
import uuid
from typing import Annotated, Any, List, Literal, Union

from fastapi import FastAPI, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

from ..datamodels import MetaInfo, PDFDoc, PDFError
from ..pdferret import PDFerret

app = FastAPI()

PydanticPDFDoc = pydantic_dataclass(PDFDoc, config=ConfigDict(arbitrary_types_allowed=True))
PydanticPDFError = pydantic_dataclass(PDFError)


class PDFerretParams(BaseModel):
    text_extractor: Union[Literal["grobid", "unstructured", "dummy"], None] = "grobid"
    meta_extractor: Union[Literal["grobid", "dummy"], None] = "grobid"
    chunker: Union[Literal["standard"], None] = "standard"
    thumbnails: Union[bool, None] = True
    llm_summary: Union[bool, None] = False
    llm_table_description: Union[bool, None] = False
    llm_model: Union[str, None] = "llama-3.2-3b-preview"
    llm_provider: Union[str, None] = "groq"

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


def _prepare_metainfo(metainfo: MetaInfo):
    metainfo.file_features.file = None
    if metainfo.thumbnail:
        metainfo.thumbnail = base64.b64encode(metainfo.thumbnail).decode("utf-8")
    return metainfo


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
        extracted, errors = extractor.extract_batch([f"{tmpdir}/{pdf.filename}" for pdf in pdfs])

    # restore original filename
    for e in extracted:
        original_filename = e.metainfo.file_features.filename.split("/")[-1]
        e.metainfo.file_features.filename = original_filename[32:]  # 32 is length of uuid
    return PDFerretResults(
        extracted=[PydanticPDFDoc(metainfo=_prepare_metainfo(e.metainfo), chunks=e.chunks) for e in extracted],
        errors=[PydanticPDFError(exc=e.exc, traceback="\n".join(e.traceback), file=str(e.file)) for e in errors],
    )
