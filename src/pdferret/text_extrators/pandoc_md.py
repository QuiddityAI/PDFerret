import glob
import os
import tempfile
from typing import List

import pypandoc

from ..base import BaseProcessor
from ..datamodels import ChunkType, PDFChunk, PDFDoc


def filter_line(line):
    # remove images from markdown
    if line.startswith("![]("):
        return True
    # remove md blocks
    if line.startswith(":::"):
        return True
    # remove empty lines
    if len(line) <= 2:
        return True


class PandocMDExtractor(BaseProcessor):
    parallel = "thread"
    operates_on = PDFDoc

    def __init__(self, lines_per_chunk=12, batch_size=None, n_proc=None):
        super().__init__(batch_size=batch_size, n_proc=n_proc)
        self.lines_per_chunk = lines_per_chunk

    def split_text_by_lines(self, text: str) -> List[str]:
        lines_per_chunk = self.lines_per_chunk
        lines = text.split("\n")
        # remove images from markdown
        lines = [line for line in lines if not filter_line(line)]
        chunks = ["\n".join(lines[i : i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]
        return chunks

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        with tempfile.TemporaryDirectory() as media_dir:
            markdown = pypandoc.convert_file(
                doc.metainfo.file_features.file,
                "markdown",
                extra_args=["--columns=130", f"--extract-media={media_dir}"],
            )

            for chunk in self.split_text_by_lines(markdown):
                if not chunk:
                    continue
                doc.chunks.append(PDFChunk(text=chunk, chunk_type=ChunkType.TEXT))

            for media in glob.glob(f"{media_dir}/**/*", recursive=True):
                if not os.path.isfile(media):
                    continue
                with open(media, "rb") as f:
                    content = f.read()
                chunk = PDFChunk(
                    text=None,
                    non_embeddable_content=content,
                    chunk_type=ChunkType.FIGURE,
                    locked=True,
                )
                doc.chunks.append(chunk)
        return doc
