import glob
import os
import tempfile
from typing import List

from ..base import BaseProcessor
from ..datamodels import ChunkType, PDFChunk, PDFDoc


def filter_line(line):
    # remove empty lines
    if len(line) <= 0:
        return True


class RawTextExtractor(BaseProcessor):
    parallel = "thread"
    operates_on = PDFDoc

    def __init__(self, lines_per_chunk=12, batch_size=None, n_proc=None):
        super().__init__(batch_size=batch_size, n_proc=n_proc)
        self.lines_per_chunk = lines_per_chunk

    def split_text_by_lines(self, text: str) -> List[str]:
        lines_per_chunk = self.lines_per_chunk
        lines = text.split("\n")
        lines = [line for line in lines if not filter_line(line)]
        chunks = ["\n".join(lines[i : i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]
        return chunks

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        with open(doc.metainfo.file_features.file, "r") as f:
            raw_text = f.read()

        for chunk in self.split_text_by_lines(raw_text):
            if not chunk:
                continue
            doc.chunks.append(PDFChunk(text=chunk, chunk_type=ChunkType.TEXT))
        return doc
