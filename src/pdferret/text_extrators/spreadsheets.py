import json
import os
import re
import tarfile
from contextlib import closing
from io import BytesIO
from typing import List

import pypandoc
from tika import parser, unpack

from pdferret.datamodels import PDFChunk, PDFDoc

from ..base import BaseProcessor
from ..datamodels import ChunkType, PDFChunk, PDFDoc

os.environ["TIKA_CLIENT_ONLY"] = "1"

prop_tags_mapping = {
    "authors": ["dc:creator", "pdf:docinfo:creator"],
    "title": ["dc:title", "pdf:docinfo:title"],
    "pub_date": [
        "xmp:CreateDate",
        "xmpMM:History:When",
        "xmp:MetadataDate",
        "dcterms:created",
        "pdf:docinfo:created",
    ],
}

doi_regex = r"\b10\.\d{4,9}/[-.;()/:\w]+"

image_extensions = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".svg",
    ".webp",
    ".emf",
    ".wmf",
    ".ico",
    ".jfif",
    ".heif",
    ".heic",
    ".dds",
    ".pcx",
    ".eps",
    ".psd",
]


def _get_by_tags(tags, meta):
    for t in tags:
        if t in meta:
            return meta[t]
    return None


def _parse_att(binary):
    with tarfile.open(fileobj=BytesIO(binary)) as tarFile:
        # get the member names
        memberNames = list(tarFile.getnames())
        attachments = {}
        for attachment in memberNames:
            attachmentMember = tarFile.getmember(attachment)
            if not attachmentMember.issym() and attachmentMember.isfile():
                with closing(tarFile.extractfile(attachmentMember)) as attachment_file:
                    attachments[attachment] = attachment_file.read()

        return attachments


def filter_line(line):
    if line.startswith("![]("):
        return True
    if line.startswith(":::"):
        return True
    if len(line) <= 2:
        return True


def split_text_by_lines(text: str, lines_per_chunk: int) -> List[str]:
    lines = text.split("\n")
    # remove images from markdown
    lines = [line for line in lines if not filter_line(line)]
    chunks = ["\n".join(lines[i : i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]
    return chunks


class TikaExtractor(BaseProcessor):
    """
    extract text and figures from PDFs using Apache Tika. Uses pandoc to convert the text to markdown.
    Additionally extracts figures.
    """

    parallel = "thread"
    operates_on = PDFDoc

    def __init__(
        self,
        tika_url,
        lines_per_chunk=15,
        tika_ocr_strategy="auto",
        save_raw_metadata=True,
        batch_size=None,
        n_proc=None,
    ):
        super().__init__(batch_size=batch_size, n_proc=n_proc)
        self.tika_url = tika_url
        if tika_ocr_strategy not in ["auto", "ocr_only", "no_ocr", "ocr_and_text_extraction"]:
            raise ValueError("Invalid Tika OCR strategy")
        self.tika_ocr_strategy = tika_ocr_strategy
        self.lines_per_chunk = lines_per_chunk
        self.save_raw_metadata = save_raw_metadata

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        headers = {"X-Tika-PDFocrStrategy": self.tika_ocr_strategy}
        parsed = parser.from_file(doc.metainfo.file_features.file, xmlContent=True, raw_response=False, headers=headers)

        if self.save_raw_metadata:
            doc.metainfo.extra_metainfo["pdf_metadata"] = parsed["metadata"]

        markdown = pypandoc.convert_text(parsed["content"], to="markdown", format="html")
        for chunk in split_text_by_lines(markdown, self.lines_per_chunk):
            if not chunk:
                continue
            doc.chunks.append(PDFChunk(text=chunk, chunk_type=ChunkType.TEXT))
        attachments = self._get_attachments(doc.metainfo.file_features.file)
        fig_chunks = self._extract_figures(attachments)
        doc.chunks.extend(fig_chunks)
        return doc

    def _extract_text(self, soup):
        p_with_text = [p for p in soup.find_all("p") if p.get_text(strip=True)]
        chunks = []
        for p in p_with_text:
            text = p.get_text(strip=True).replace("\n", " ")
            text = re.sub(r"\s+", " ", text)
            chunk = PDFChunk(section=text, chunk_type=ChunkType.OTHER)
            chunks.append(chunk)
        return chunks

    def _extract_tables(self, soup):
        tables = soup.find_all("table")
        chunks = []
        for table in tables:
            table_html = str(table)
            chunk = PDFChunk(non_embeddable_content=table_html, chunk_type=ChunkType.OTHER, locked=True)
            chunk.requires_fill = True
            chunks.append(chunk)
        return chunks

    def _extract_figures(self, attachments):
        chunks = []
        for attachment_name, attachment in attachments.items():
            if not any([attachment_name.endswith(ext) for ext in image_extensions]):
                continue
            chunk = PDFChunk(
                non_embeddable_content=attachment,
                chunk_type=ChunkType.FIGURE,
                locked=True,
            )
            chunk.requires_fill = True
            chunks.append(chunk)
        return chunks

    def _parse_metadata(self, tika_meta):
        result = {}
        for prop, tags in prop_tags_mapping.items():
            val = _get_by_tags(tags, tika_meta)
            if val:
                result[prop] = val

        dois = re.findall(doi_regex, json.dumps(tika_meta))
        if dois:
            result["doi"] = dois[0]
        if "authors" in result:
            result["authors"] = self._standardize_authors(result["authors"])
        return result

    def _standardize_authors(self, authors):
        if isinstance(authors, list):
            return authors
        else:
            return authors.split(";")

    def _get_attachments(self, file):
        headers = {"X-Tika-PDFextractInlineImages": "true", "X-Tika-PDFocrStrategy": "AUTO"}
        code, binary = unpack.parse1(
            "unpack",
            file,
            self.tika_url,
            responseMimeType="application/x-tar",
            headers=headers,
            services={"meta": "/meta", "text": "/tika", "all": "/rmeta/xml", "unpack": "/unpack"},
            rawResponse=True,
            requestOptions={},
        )
        if code != 200:
            raise ValueError(f"Bad return code, {code}")
        return _parse_att(binary)
