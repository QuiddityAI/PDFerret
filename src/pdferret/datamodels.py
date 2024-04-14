from dataclasses import dataclass, field
from typing import List, Tuple, Union, BinaryIO, TypeAlias

PDFFile: TypeAlias = Union[str, BinaryIO]


@dataclass
class PDFChunk:
    page: int = None
    coordinates: List[Tuple[int]] = None
    section: str = ""
    prefix: str = ""
    text: str = ""
    suffix: str = ""


@dataclass
class FileFeatures:
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
