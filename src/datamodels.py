from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class PDFChunk:
    page: int = None
    coordinates: List[Tuple[int]] = None
    section: str = ""
    prefix: str = ""
    text: str = ""
    suffix: str = ""


@dataclass
class MetaInfo:
    title: str = ""
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    pub_date: str = ""


@dataclass
class PDFDoc:
    metainfo: MetaInfo
    chunks: List[PDFChunk]
