from dataclasses import dataclass, field
from enum import Enum
from typing import BinaryIO, List, Tuple, TypeAlias, Union

PDFFile: TypeAlias = Union[str, BinaryIO, bytes]


# enum for different types of document elements, such as text, figure, table, etc.
class ChunkType(Enum):
    TEXT = "text"
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    OTHER = "other"


@dataclass
class PDFError:
    exc: str = ""
    traceback: Union[str, List[str]] = ""
    file: str = ""


@dataclass
class PDFChunk:
    page: int = None
    coordinates: List[Tuple[float, float]] = None
    section: str = ""
    prefix: str = ""
    text: str = ""
    suffix: str = ""
    locked: bool = False
    chunk_type: ChunkType = ChunkType.TEXT
    # true if joining of this chunk with others is forbidden, e.g. fro figure captions


@dataclass
class FileFeatures:
    filename: str = ""
    file: PDFFile = None
    is_scanned: bool = None


@dataclass
class MetaInfo:
    doi: str = ""
    title: str = ""
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    pub_date: str = ""
    language: str = ""
    file_features: FileFeatures = None
    npages: int = None


@dataclass
class PDFDoc:
    metainfo: MetaInfo = field(default_factory=MetaInfo)
    chunks: List[PDFChunk] = field(default_factory=lambda: [PDFChunk()])
