import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, TypeAlias

import requests
from pydantic import BaseModel, ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass

PDFFile: TypeAlias = str


class ChunkType(str, Enum):
    TEXT = "text"
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    OTHER = "other"


@pydantic_dataclass
class PDFError:
    exc: str = ""
    traceback: str | list[str] = ""
    file: str = ""


@pydantic_dataclass
class PDFChunk:
    page: int | None = None
    coordinates: List[Tuple[float, float]] | None = None
    section: str | None = None
    prefix: str | None = None
    text: str | None = None
    suffix: str | None = None
    locked: bool | None = None
    chunk_type: ChunkType | None = ChunkType.TEXT


@pydantic_dataclass
class FileFeatures:
    filename: str = ""
    file: PDFFile | None = None
    is_scanned: bool = None


@pydantic_dataclass
class MetaInfo:
    doi: str = ""
    title: str = ""
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    pub_date: str = ""
    language: str = ""
    file_features: FileFeatures | None = None
    npages: int | None = None
    thumbnail: bytes | None = None


@pydantic_dataclass
class PDFDoc:
    metainfo: MetaInfo = field(default_factory=MetaInfo)
    chunks: List[PDFChunk] = field(default_factory=lambda: [PDFChunk()])


class PDFerretResults(BaseModel):
    extracted: List[PDFDoc]
    errors: List[PDFError]


class PDFerretClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def process_files(
        self, pdf_paths: List[str], text_extractor="grobid", meta_extractor="grobid", chunker="standard"
    ) -> PDFerretResults:
        """
        Process a list of PDF files using the PDFerret API.

        Args:
            pdf_paths: List of paths to the PDF files to process.
            text_extractor: The text extractor to use. Options are "grobid" and "unstructured". Defaults to "grobid".
            meta_extractor: The metadata extractor to use. Options are "grobid". Defaults to "grobid".
            chunker: The chunker to use. Options are "standard". Defaults to "standard".

        Returns:
            A JSON response from the PDFerret API with the extracted data.
        """
        url = f"{self.base_url}/process_files_by_stream"
        files = [("pdfs", (open(pdf_path, "rb"))) for pdf_path in pdf_paths]
        data = {
            "params": json.dumps(
                {"text_extractor": text_extractor, "meta_extractor": meta_extractor, "chunker": chunker}
            )
        }
        response = requests.post(url, files=files, data=data)

        if response.status_code == 200:
            return PDFerretResults.parse_obj(response.json())
        else:
            try:
                error = response.json()
            except Exception as e:
                response.raise_for_status()
            raise ValueError(error)
