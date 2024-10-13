import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
import pdferret  # noqa: E402
from pdferret.datamodels import MetaInfo, PDFDoc  # noqa: E402
from pdferret.metainfo.llm_extractor import LLMMetaExtractor  # noqa: E402


@pytest.fixture
def sample_pdf_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test.pdf")


@pytest.fixture
def sample_doc_german_path():
    abspath = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(abspath, "data/test_de.doc")


@pytest.fixture
@patch("pdferret.metainfo.llm_extractor.LLMonkey")
def extractor(MockLLMonkey):
    mock_llmonkey = MockLLMonkey.return_value
    extractor = LLMMetaExtractor()
    return extractor, mock_llmonkey


def test_process_single_with_no_abstract(extractor):
    extractor, mock_llmonkey = extractor
    pdfdoc = PDFDoc(metainfo=MetaInfo(abstract=None, file_features=MagicMock(filename="test.pdf")), chunks=[])
    mock_llmonkey.generate_structured_response.return_value = (MagicMock(summary="Test summary"), None)

    result = extractor.process_single(pdfdoc)

    assert result.metainfo.abstract == "Test summary"
    mock_llmonkey.generate_structured_response.assert_called_once()


def test_process_single_with_force_overwrite(extractor):
    extractor, mock_llmonkey = extractor
    pdfdoc = PDFDoc(metainfo=MetaInfo(abstract="Old summary", file_features=MagicMock(filename="test.pdf")), chunks=[])
    extractor.force_overwrite = True
    mock_llmonkey.generate_structured_response.return_value = (MagicMock(summary="New summary"), None)

    result = extractor.process_single(pdfdoc)

    assert result.metainfo.abstract == "New summary"
    mock_llmonkey.generate_structured_response.assert_called_once()


def test_process_single_with_existing_abstract_no_overwrite(extractor):
    extractor, mock_llmonkey = extractor
    pdfdoc = PDFDoc(
        metainfo=MetaInfo(abstract="Existing summary", file_features=MagicMock(filename="test.pdf")), chunks=[]
    )
    extractor.force_overwrite = False

    result = extractor.process_single(pdfdoc)

    assert result.metainfo.abstract == "Existing summary"
    mock_llmonkey.generate_structured_response.assert_not_called()


def test_generate_llm_abstract_with_chunks(extractor):
    extractor, mock_llmonkey = extractor
    chunks = [MagicMock(text=f"Chunk {i}") for i in range(3)]
    pdfdoc = PDFDoc(metainfo=MetaInfo(file_features=MagicMock(filename="test.pdf")), chunks=chunks)
    mock_llmonkey.generate_structured_response.return_value = (MagicMock(summary="Generated summary"), None)

    summary = extractor._generate_llm_abstract(pdfdoc)

    assert summary == "Generated summary"
    mock_llmonkey.generate_structured_response.assert_called_once()


def test_generate_llm_abstract_no_chunks(extractor):
    extractor, mock_llmonkey = extractor
    pdfdoc = PDFDoc(metainfo=MetaInfo(file_features=MagicMock(filename="test.pdf")), chunks=[])
    mock_llmonkey.generate_structured_response.return_value = (MagicMock(summary="Generated summary"), None)

    summary = extractor._generate_llm_abstract(pdfdoc)

    assert summary == "Generated summary"
    mock_llmonkey.generate_structured_response.assert_called_once()


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
    kwds = ["sierra leone", "diamanten", "konflikt"]
    assert all([kwd in parsed[0].metainfo.abstract.lower() for kwd in kwds])
