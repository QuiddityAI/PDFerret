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


def test_extract_pdf_unstructured(sample_pdf_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured")
    parsed, errors = pdferret_instance.extract_batch([sample_pdf_path])
    assert not errors
    assert len(parsed) == 1
    assert "Transformer follows this overall architecture" in parsed[0].chunks[10].text
    assert parsed[0].metainfo.file_features.file == sample_pdf_path


def test_extract_docx_unstructured(sample_docx_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured")
    parsed, errors = pdferret_instance.extract_batch([sample_docx_path])
    assert not errors
    assert len(parsed) == 1
    assert parsed[0].metainfo.file_features.file == sample_docx_path


def test_extract_html_unstructured(sample_html_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured")
    parsed, errors = pdferret_instance.extract_batch([sample_html_path])
    assert not errors
    assert len(parsed) == 1
    assert parsed[0].metainfo.file_features.file == sample_html_path


def test_extract_pptx_unstructured(sample_pptx_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured")
    parsed, errors = pdferret_instance.extract_batch([sample_pptx_path])
    assert not errors
    assert len(parsed) == 1
    assert parsed[0].metainfo.file_features.file == sample_pptx_path


def test_extract_docx_w_table_unstructured(sample_docx_w_table_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured")
    parsed, errors = pdferret_instance.extract_batch([sample_docx_w_table_path])
    assert not errors
    assert len(parsed) == 1
    assert len([ch for ch in parsed[0].chunks if ch.chunk_type.value == "table"]) == 2
    assert parsed[0].metainfo.file_features.file == sample_docx_w_table_path


def test_extract_doc_unstructured(sample_doc_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured")
    parsed, errors = pdferret_instance.extract_batch([sample_doc_path])
    assert not errors
    assert len(parsed) == 1
    assert parsed[0].metainfo.file_features.file == sample_doc_path


def test_extract_doc_german(sample_doc_german_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured")
    parsed, errors = pdferret_instance.extract_batch([sample_doc_german_path])
    assert not errors
    assert len(parsed) == 1
    assert "Kommunalbehörden in der Europäischen Gemeinschaft" in parsed[0].chunks[10].text
