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

    def _split_chunk(self, chunk: str, chunk_dict: dict) -> list[PDFChunk]:
        # splits chunk into smaller chunks
        # of approximately equal length with overlap
        if len(chunk) <= MAX_CHUNK_LEN:
            return [PDFChunk(**(chunk_dict | dict(text=chunk)))]
        cutted = []
        n_segments = int(np.ceil((len(chunk) / MAX_CHUNK_LEN)))
        segment_size = len(chunk) // n_segments
        for segment in range(n_segments):
            if segment == 0:
                start = 0
                end = segment_size
                cutted.append(
                    PDFChunk(**(chunk_dict | dict(text=chunk[start:end], suffix=chunk[end : end + CHUNK_OVERLAP])))
                )
            elif segment == (n_segments - 1):
                start = end
                end = -1
                cutted.append(
                    PDFChunk(**(chunk_dict | dict(text=chunk[start:end], prefix=chunk[start - CHUNK_OVERLAP : start])))
                )
            else:
                start = end
                end = end + segment_size
                cutted.append(
                    PDFChunk(
                        **(
                            chunk_dict
                            | dict(
                                text=chunk[start:end],
                                prefix=chunk[start - CHUNK_OVERLAP : start],
                                suffix=chunk[end : end + CHUNK_OVERLAP],
                            )
                        )
                    )
                )
        return cutted

    def process_single_old(self, doc: PDFDoc) -> PDFDoc:
        # firstly build fulltext before chunking which will cause overlaps
        full_text = ""
        for chunk_obj in doc.chunks:
            if chunk_obj.chunk_type == ChunkType.TEXT:
                full_text += chunk_obj.text + "\n"
            elif chunk_obj.chunk_type == ChunkType.TABLE:
                full_text += chunk_obj.non_embeddable_content + "\n"
                full_text += (chunk_obj.text + "\n") if chunk_obj.text else ""
        output_chunks = []
        buffer = ""
        for chunk_obj in doc.chunks:
            chunk = chunk_obj.text
            if not chunk:
                continue
            chunk_dict = asdict(chunk_obj)
            print(f"Processing chunk: {chunk[:50]}...")  # Debug print
            # If the chunk is locked or it's not text, just append it to the output, don't mix it with other chunks
            if chunk_obj.locked or chunk_obj.chunk_type != ChunkType.TEXT:
                print(f"Chunk is locked or not text: {chunk_obj.chunk_type}")  # Debug print
                if buffer:  # if there's something in the buffer, append it to the output
                    # to avoid mixing locked chunks with text chunks
                    output_chunks.append(PDFChunk(**(chunk_dict | dict(text=buffer))))
                    buffer = ""
                output_chunks.append(chunk_obj)
                continue
            if len(chunk) > MAX_CHUNK_LEN:
                print(f"Chunk is too long: {len(chunk)}")  # Debug print
                subchunks = self._split_chunk(chunk)
                output_chunks.extend(self._handle_subchunks(subchunks, chunk_dict))
            elif len(chunk) < 0.5 * MAX_CHUNK_LEN:
                print(f"Chunk is too short: {len(chunk)}")  # Debug print
                buffer += chunk
                if len(buffer) >= 0.5 * MAX_CHUNK_LEN:
                    print(f"Buffer reached half max chunk length: {len(buffer)}")  # Debug print
                    if len(buffer) > MAX_CHUNK_LEN:
                        print(f"Buffer is too long: {len(buffer)}")  # Debug print
                        subchunks = self._split_chunk(buffer)
                        output_chunks.extend(self._handle_subchunks(subchunks, chunk_dict))
                        buffer = ""
                    else:
                        output_chunks.append(PDFChunk(**(chunk_dict | dict(text=buffer))))
                    buffer = ""
            else:
                output_chunks.append(PDFChunk(**(chunk_dict | dict(text=chunk))))

        if buffer:
            print(f"Appending remaining buffer: {buffer[:50]}...")  # Debug print
            output_chunks.append(PDFChunk(**(chunk_dict | dict(text=buffer))))

        return PDFDoc(metainfo=doc.metainfo, chunks=output_chunks, full_text=full_text)

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        # firstly build fulltext before chunking which will cause overlaps
        full_text = ""
        for chunk_obj in doc.chunks:
            if chunk_obj.chunk_type == ChunkType.TEXT:
                full_text += chunk_obj.text + "\n"
            elif chunk_obj.chunk_type == ChunkType.TABLE:
                full_text += chunk_obj.non_embeddable_content + "\n"
                full_text += (chunk_obj.text + "\n") if chunk_obj.text else ""

        output_chunks = []
        buffer = ""
        chunk_dict = None

        # Combine all text chunks into a single buffer
        for chunk_obj in doc.chunks:
            text_chunk = chunk_obj.text
            if not text_chunk:
                continue
            chunk_dict = asdict(chunk_obj)
            # If the chunk is locked or it's not text, just append it to the output, don't mix it with other chunks
            if chunk_obj.locked or chunk_obj.chunk_type != ChunkType.TEXT:
                if buffer:
                    subchunks = self._split_chunk(buffer, chunk_dict)
                    output_chunks.extend(subchunks)
                    buffer = ""
                output_chunks.append(chunk_obj)
            else:
                buffer += " " + text_chunk

        # Split the combined buffer into subchunks and handle them
        if buffer:
            output_chunks.extend(self._split_chunk(buffer, chunk_dict))

        return PDFDoc(metainfo=doc.metainfo, chunks=output_chunks, full_text=full_text)
