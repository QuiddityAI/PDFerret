from dataclasses import asdict
import os
import numpy as np
from .base import BaseProcessor
from .datamodels import ChunkType, PDFChunk, PDFDoc


MAX_CHUNK_LEN = int(os.environ.get("PDFERRET_MAX_CHUNK_LEN", 2000))
CHUNK_OVERLAP = int(os.environ.get("PDFERRET_CHUNK_OVERLAP", 100))


class SimpleChunker(BaseProcessor):
    parallel = False
    operates_on = PDFDoc

    def _split_chunk(self, chunk):
        # splits chunk into smaller chunks
        # of approximately equal length with overlap
        if len(chunk) <= MAX_CHUNK_LEN:
            return [chunk]
        cutted = []
        n_segments = int(np.ceil((len(chunk) / MAX_CHUNK_LEN)))
        segment_size = (len(chunk) // n_segments) - CHUNK_OVERLAP
        for segment in range(n_segments):
            if segment == 0:
                start = 0
                end = segment_size + CHUNK_OVERLAP
            elif segment == (n_segments - 1):
                start = end - CHUNK_OVERLAP
                end = len(chunk)
            else:
                start = end - CHUNK_OVERLAP
                end = end + segment_size + CHUNK_OVERLAP
            cutted.append(chunk[start:end])
        return cutted

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        # firstly build fulltext before chunking which will cause overlaps
        full_text = ""
        for chunk_obj in doc.chunks:
            if chunk_obj.chunk_type == ChunkType.TEXT:
                full_text += chunk_obj.text + "\n"
            elif chunk_obj.chunk_type == ChunkType.TABLE:
                full_text += chunk_obj.non_embeddable_content + "\n"
        output_chunks = []
        buffer = ""
        for chunk_obj in doc.chunks:
            chunk = chunk_obj.text
            chunk_dict = asdict(chunk_obj)
            # If the chunk is locked or it's not text, just append it to the output, don't mix it with other chunks
            if chunk_obj.locked or chunk_obj.chunk_type != ChunkType.TEXT:
                if buffer:  # if there's something in the buffer, append it to the output
                    # to avoid mixing locked chunks with text chunks
                    output_chunks.append(PDFChunk(**(chunk_dict | dict(text=buffer))))
                    buffer = ""
                output_chunks.append(chunk_obj)
                continue
            if len(chunk) > MAX_CHUNK_LEN:
                subchunks = self._split_chunk(chunk)
                for subchunk in subchunks:
                    output_chunks.append(PDFChunk(**(chunk_dict | dict(text=subchunk))))
            elif len(chunk) < 0.5 * MAX_CHUNK_LEN:
                buffer += " " + chunk
                if len(buffer) >= 0.5 * MAX_CHUNK_LEN:
                    if len(buffer) > MAX_CHUNK_LEN:
                        subchunks = self._split_chunk(buffer)
                        for subchunk in subchunks:
                            output_chunks.append(PDFChunk(**(chunk_dict | dict(text=subchunk))))
                        buffer = ""
                    else:
                        output_chunks.append(PDFChunk(**(chunk_dict | dict(text=buffer))))
                    buffer = ""
            else:
                output_chunks.append(PDFChunk(**(chunk_dict | dict(text=chunk))))

        if buffer:
            output_chunks.append(PDFChunk(**(chunk_dict | dict(text=buffer))))

        return PDFDoc(metainfo=doc.metainfo, chunks=output_chunks, full_text=full_text)
