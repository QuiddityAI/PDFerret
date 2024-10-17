import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import pdferret  # noqa: E402


@pytest.fixture
def sample_pdf_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test.pdf")


@pytest.fixture
def sample_doc_german_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test_de.doc")


@pytest.fixture
def sample_docx_w_table_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test_w_table.docx")


def test_full_generate_summary(sample_pdf_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured", llm_summary=True)
    parsed, errors = pdferret_instance.extract_batch([sample_pdf_path])
    assert not errors
    kwds = ["Transformer", "attention", "translation"]
    assert all([kwd in parsed[0].metainfo.abstract for kwd in kwds])


def test_full_generate_summary_german(sample_doc_german_path):
    pdferret_instance = pdferret.PDFerret(meta_extractor="dummy", text_extractor="unstructured", llm_summary=True)
    parsed, errors = pdferret_instance.extract_batch([sample_doc_german_path])
    assert not errors
    kwds = ["sierra leone", "diamanten", "angola"]
    assert all([kwd in parsed[0].metainfo.abstract.lower() for kwd in kwds])


def test_llm_table_description(sample_docx_w_table_path):
    pdferret_instance = pdferret.PDFerret(
        meta_extractor="dummy",
        text_extractor="unstructured",
        llm_summary=False,
        llm_table_description=True,
        thumbnails=False,
    )
    parsed, errors = pdferret_instance.extract_batch([sample_docx_w_table_path])
    tables = [ch for ch in parsed[0].chunks if ch.chunk_type.value == "table"]
    assert len(tables) == 2
    assert "screen reader" in tables[0].text.lower()
    assert "screen reader" in tables[1].text.lower()
