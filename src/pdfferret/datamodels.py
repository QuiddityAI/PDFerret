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
    npages: int = None
    is_scanned: bool = None


@dataclass
class MetaInfo:
    title: str = ""
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    pub_date: str = ""
    language: str = ""
    file_features: FileFeatures = None


@dataclass
class PDFDoc:
    metainfo: MetaInfo
    chunks: List[PDFChunk]
