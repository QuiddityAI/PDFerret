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
