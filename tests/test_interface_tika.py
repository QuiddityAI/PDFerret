import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import pdferret  # noqa: E402


# fixture returning sample pdf document
@pytest.fixture
def sample_pdf_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test.pdf")


@pytest.fixture
def sample_docx_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test.docx")


@pytest.fixture
def sample_html_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test.html")


@pytest.fixture
def sample_pptx_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test.pptx")


@pytest.fixture
def sample_docx_w_table_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test_w_table.docx")


@pytest.fixture
def sample_doc_german_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test_de.doc")


@pytest.fixture
def sample_doc_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test.doc")


def test_extract_pdf_tika(sample_pdf_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="tika")
    parsed, errors = pdferret_instance.extract_batch([sample_pdf_path])
    assert not errors
    assert len(parsed) == 1
    assert "Transformer follows this overall architecture" in parsed[0].chunks[10].text
    assert parsed[0].metainfo.file_features.file == sample_pdf_path
    fig_chunks = [ch for ch in parsed[0].chunks if ch.chunk_type.value == "figure"]
    assert len(fig_chunks) > 0


def test_extract_docx_tika(sample_docx_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="tika", general_extractor="tika")
    parsed, errors = pdferret_instance.extract_batch([sample_docx_path])
    assert not errors
    assert len(parsed) == 1
    assert parsed[0].metainfo.file_features.file == sample_docx_path
    fig_chunks = [ch for ch in parsed[0].chunks if ch.chunk_type.value == "figure"]
    assert len(fig_chunks) > 0


def test_extract_pptx_tika(sample_pptx_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="tika", general_extractor="tika")
    parsed, errors = pdferret_instance.extract_batch([sample_pptx_path])
    assert not errors
    assert len(parsed) == 1
    assert parsed[0].metainfo.file_features.file == sample_pptx_path
    fig_chunks = [ch for ch in parsed[0].chunks if ch.chunk_type.value == "figure"]
    assert len(fig_chunks) > 0


def test_extract_docx_w_table_tika(sample_docx_w_table_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="tika", general_extractor="tika")
    parsed, errors = pdferret_instance.extract_batch([sample_docx_w_table_path])
    assert not errors
    assert len(parsed) == 1
    assert len([ch for ch in parsed[0].chunks if ch.chunk_type.value == "table"]) == 2
    assert parsed[0].metainfo.file_features.file == sample_docx_w_table_path
    fig_chunks = [ch for ch in parsed[0].chunks if ch.chunk_type.value == "figure"]
    assert len(fig_chunks) > 0


def test_extract_doc_tika(sample_doc_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="tika", general_extractor="tika")
    parsed, errors = pdferret_instance.extract_batch([sample_doc_path])
    assert not errors
    assert len(parsed) == 1
    assert parsed[0].metainfo.file_features.file == sample_doc_path


def test_extract_doc_german_tika(sample_doc_german_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="tika", general_extractor="tika")
    parsed, errors = pdferret_instance.extract_batch([sample_doc_german_path])
    assert not errors
    assert len(parsed) == 1
    assert "Das Zertifikationssystem ist im Grunde eine Regelung" in parsed[0].chunks[10].text
    fig_chunks = [ch for ch in parsed[0].chunks if ch.chunk_type.value == "figure"]
    assert len(fig_chunks) > 0
