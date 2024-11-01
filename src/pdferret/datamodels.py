from dataclasses import dataclass, field
from enum import Enum
from typing import BinaryIO, List, Tuple, TypeAlias, Union

PDFFile: TypeAlias = str


# enum for different types of document elements, such as text, figure, table, etc.
class ChunkType(Enum):
    TEXT = "text"
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    VISUAL_PAGE = "visual_page"
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
    non_embeddable_content: str = ""
    text: str = ""
    suffix: str = ""
    locked: bool = False
    chunk_type: ChunkType = ChunkType.TEXT
    # true if joining of this chunk with others is forbidden, e.g. fro figure captions
    # hiddenattributes:
    # reliable - if the text is reliable and don't need to be cleaned
    # requires_fill - if the text requires filling from the metadata (e.g. with llm)


@dataclass
class FileFeatures:
    filename: str = ""
    file: PDFFile = None
    is_scanned: bool = None


@dataclass
class MetaInfo:
    doi: str = ""
    title: str = ""
    document_type: str = ""
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    pub_date: str = ""
    mentioned_date: str = ""
    language: str = ""
    detected_language: str = ""
    file_features: FileFeatures = None
    npages: int = None
    thumbnail: bytes | str = None
    extra_metainfo: dict = field(default_factory=dict)
    ai_metadata: str = ""


@dataclass
class PDFDoc:
    metainfo: MetaInfo = field(default_factory=MetaInfo)
    chunks: List[PDFChunk] = field(default_factory=lambda: [])
