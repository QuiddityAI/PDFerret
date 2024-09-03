from ..pdferret import PDFerret
from ..datamodels import PDFDoc, PDFError, MetaInfo
from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.dataclasses import dataclass as pydantic_dc
from dataclasses import asdict
from typing import Union, List, Annotated, Any, Literal
from fastapi import FastAPI, UploadFile, Form, File
import json
import uvicorn
import uuid
import tempfile

app = FastAPI()

PydanticPDFDoc = pydantic_dc(PDFDoc, config=ConfigDict(arbitrary_types_allowed=True))
PydanticPDFError = pydantic_dc(PDFError)


class PDFerretParams(BaseModel):
    text_extractor: Union[Literal["grobid", "unstructured"], None] = "grobid"
    meta_extractor: Union[Literal["grobid"], None] = "grobid"
    chunker: Union[Literal["standard"], None] = "standard"

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


def _clear_file(metainfo: MetaInfo):
    metainfo.file_features.file = None
    return metainfo


@app.post("/process_files_by_path")
def process_files_by_path(pdfs: List[str], params: PDFerretParams) -> PDFerretResults:
    extractor = PDFerret(**params.dict())
    extracted, errors = extractor.extract_batch(pdfs)
    return PDFerretResults(
        extracted=[PydanticPDFDoc(metainfo=e.metainfo, chunks=e.chunks) for e in extracted],
        errors=[PydanticPDFError(exc=e.exc, traceback="\n".join(e.traceback), file=str(e.file)) for e in errors],
    )


@app.post("/process_files_by_stream")
def process_files_by_stream(
    pdfs: Annotated[List[UploadFile], File()], params: Annotated[PDFerretParams, Form()]
) -> PDFerretResults:

    extractor = PDFerret(**params.dict())

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
        extracted=[PydanticPDFDoc(metainfo=_clear_file(e.metainfo), chunks=e.chunks) for e in extracted],
        errors=[PydanticPDFError(exc=e.exc, traceback="\n".join(e.traceback), file=str(e.file)) for e in errors],
    )
