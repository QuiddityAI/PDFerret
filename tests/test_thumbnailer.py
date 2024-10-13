import os
import sys
from unittest.mock import mock_open, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from pdferret.datamodels import FileFeatures, MetaInfo  # noqa: E402
from pdferret.thumbnails.libreoffice import LibreOfficeThumbnailer  # noqa: E402
from pdferret.thumbnails.pdf import PDFiumThumbnailer  # noqa: E402
from pdferret.thumbnails.thumbnailer import Thumbnailer  # noqa: E402


@pytest.fixture
def sample_docx_meta_info():
    fname = "data/test.docx"
    fname = os.path.abspath(os.path.join(os.path.dirname(__file__), fname))
    return MetaInfo(file_features=FileFeatures(file=fname))


@pytest.fixture
def sample_pdf_meta_info():
    fname = "data/test.pdf"
    fname = os.path.abspath(os.path.join(os.path.dirname(__file__), fname))
    return MetaInfo(file_features=FileFeatures(file=fname))


def test_libreoffice_thumbnailer(sample_docx_meta_info):
    thumbnailer = LibreOfficeThumbnailer()
    X = {"test": sample_docx_meta_info}
    processed_X, errors = thumbnailer.process_batch(X)
    assert not errors
    assert "test" in processed_X
    assert b"\x89PNG" in processed_X["test"].thumbnail


def test_pdfium_thumbnailer(sample_pdf_meta_info):
    thumbnailer = PDFiumThumbnailer()
    X = {"test": sample_pdf_meta_info}
    processed_X, errors = thumbnailer._process_batch(X)
    assert not errors
    assert "test" in processed_X
    assert b"\x89PNG" in processed_X["test"].thumbnail


def test_main_thumbnailer(sample_docx_meta_info, sample_pdf_meta_info):
    thumbnailer = Thumbnailer()
    X = {"test.docx": sample_docx_meta_info, "test.pdf": sample_pdf_meta_info}
    processed_X, errors = thumbnailer.process_batch(X)
    assert not errors
    assert "test.docx" in processed_X
    assert "test.pdf" in processed_X
    assert b"\x89PNG" in processed_X["test.docx"].thumbnail
    assert b"\x89PNG" in processed_X["test.pdf"].thumbnail
