import base64
import json
import os
import re
import tarfile
from contextlib import closing
from io import BytesIO

import tika
from bs4 import BeautifulSoup
from tika import parser, unpack

from pdferret.datamodels import PDFChunk, PDFDoc

from ..base import BaseProcessor
from ..datamodels import ChunkType, MetaInfo, PDFChunk, PDFDoc

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


class TikaExtractor(BaseProcessor):
    parallel = "thread"
    operates_on = MetaInfo

    def __init__(self, tika_url, batch_size=None, n_proc=None):
        super().__init__(batch_size=batch_size, n_proc=n_proc)
        self.tika_url = tika_url

    def process_single(self, meta: MetaInfo) -> PDFDoc:
        parsed = parser.from_file(meta.file_features.file, xmlContent=True, raw_response=False)
        soup = BeautifulSoup(parsed["content"])
        extracted_meta = self._parse_metadata(parsed["metadata"])
        meta.__dict__.update(extracted_meta)  # update the meta info with the extracted metadata
        chunks = []
        chunks.extend(self._extract_text(soup))
        chunks.extend(self._extract_tables(soup))
        attachments = self._get_attachments(meta.file_features.file)
        fig_chunks = self._extract_figures(attachments)
        chunks.extend(fig_chunks)
        return PDFDoc(chunks=chunks, metainfo=meta)

    def _extract_text(self, soup):
        p_with_text = [p for p in soup.find_all("p") if p.get_text(strip=True)]
        chunks = []
        for p in p_with_text:
            text = p.get_text(strip=True).replace("\n", " ")
            text = re.sub(r"\s+", " ", text)
            chunk = PDFChunk(text=text, chunk_type=ChunkType.TEXT)
            chunks.append(chunk)
        return chunks

    def _extract_tables(self, soup):
        tables = soup.find_all("table")
        chunks = []
        for table in tables:
            table_html = str(table)
            chunk = PDFChunk(non_embeddable_content=table_html, chunk_type=ChunkType.TABLE, locked=True)
            chunk.requires_fill = True
            chunks.append(chunk)
        return chunks

    def _extract_figures(self, attachments):
        chunks = []
        for attachment_name, attachment in attachments.items():
            if not any([attachment_name.endswith(ext) for ext in image_extensions]):
                continue
            chunk = PDFChunk(
                non_embeddable_content=base64.b64encode(attachment).decode("ascii"),
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
