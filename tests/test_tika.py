import json
import os
import sys
from enum import Enum

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import dataclasses

from pdferret.datamodels import FileFeatures, MetaInfo, PDFDoc  # noqa: E402
from pdferret.text_extrators.tika import TikaExtractor  # noqa: E402


@pytest.fixture
def tika_extractor():
    return TikaExtractor(tika_url="http://localhost:9998")


@pytest.fixture
def meta_info():
    abspath = os.path.abspath(os.path.dirname(__file__))
    file = os.path.join(abspath, "data/test.pdf")
    file_features = FileFeatures(file=file)
    return MetaInfo(file_features=file_features)


@pytest.fixture
def meta_info_w_table():
    abspath = os.path.abspath(os.path.dirname(__file__))
    file = os.path.join(abspath, "data/test_w_table.docx")
    file_features = FileFeatures(file=file)
    return MetaInfo(file_features=file_features)


def test_process_single(tika_extractor, meta_info):
    result = tika_extractor.process_single(meta_info)
    assert isinstance(result, PDFDoc)
    assert len(result.chunks) > 0


def test_extract_text(tika_extractor, meta_info):
    parsed = tika_extractor.process_single(meta_info)
    text_chunks = [chunk for chunk in parsed.chunks if chunk.chunk_type.value == "text"]
    assert len(text_chunks) > 0
    assert all(isinstance(chunk.text, str) for chunk in text_chunks)


def test_extract_tables(tika_extractor, meta_info_w_table):
    parsed = tika_extractor.process_single(meta_info_w_table)
    table_chunks = [chunk for chunk in parsed.chunks if chunk.chunk_type.value == "table"]
    assert len(table_chunks) > 0
    assert all(isinstance(chunk.non_embeddable_content, str) for chunk in table_chunks)


def test_extract_figures(tika_extractor, meta_info):
    parsed = tika_extractor.process_single(meta_info)
    figure_chunks = [chunk for chunk in parsed.chunks if chunk.chunk_type.value == "figure"]
    assert len(figure_chunks) > 0
    assert all(isinstance(chunk.non_embeddable_content, bytes) for chunk in figure_chunks)


def custom_asdict_factory(data):
    def convert_value(obj):
        if isinstance(obj, Enum):
            return obj.value
        return obj

    return dict((k, convert_value(v)) for k, v in data)


def test_parse_metadata(tika_extractor, meta_info):
    parsed = tika_extractor.process_single(meta_info)
    meta = parsed.metainfo
    assert meta.authors is not None
    assert meta.title is not None
    assert meta.pub_date is not None
    assert meta.doi is not None
    # with open("./tmp.json", "w") as f:
    #     f.write(json.dumps(dataclasses.asdict(parsed, dict_factory=custom_asdict_factory), indent=4))
