import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from pdferret.datamodels import FileFeatures, MetaInfo, PDFDoc  # noqa: E402
from pdferret.thumbnails.libreoffice import LibreOfficeThumbnailer  # noqa: E402
from pdferret.thumbnails.pdf import PDFiumThumbnailer  # noqa: E402
from pdferret.thumbnails.thumbnailer import Thumbnailer  # noqa: E402


@pytest.fixture
def sample_pdfdoc_pdf():
    fname = "data/test.pdf"
    fname = os.path.abspath(os.path.join(os.path.dirname(__file__), fname))
    return PDFDoc(metainfo=MetaInfo(file_features=FileFeatures(file=fname)))


@pytest.fixture
def sample_pdfdoc_docx():
    fname = "data/test.docx"
    fname = os.path.abspath(os.path.join(os.path.dirname(__file__), fname))
    return PDFDoc(metainfo=MetaInfo(file_features=FileFeatures(file=fname)))


def test_libreoffice_thumbnailer(sample_pdfdoc_docx):
    thumbnailer = LibreOfficeThumbnailer()
    X = {"test": sample_pdfdoc_docx}
    processed_X, errors = thumbnailer.process_batch(X)
    assert not errors
    assert "test" in processed_X
    assert b"\x89PNG" in processed_X["test"].metainfo.thumbnail


def test_pdfium_thumbnailer(sample_pdfdoc_pdf):
    thumbnailer = PDFiumThumbnailer()
    X = {"test": sample_pdfdoc_pdf}
    processed_X, errors = thumbnailer._process_batch(X)
    assert not errors
    assert "test" in processed_X
    assert b"\x89PNG" in processed_X["test"].metainfo.thumbnail


def test_main_thumbnailer(sample_pdfdoc_docx, sample_pdfdoc_pdf):
    thumbnailer = Thumbnailer()
    X = {"test.docx": sample_pdfdoc_docx, "test.pdf": sample_pdfdoc_pdf}
    processed_X, errors = thumbnailer.process_batch(X)
    assert not errors
    assert "test.docx" in processed_X
    assert "test.pdf" in processed_X
    assert b"\x89PNG" in processed_X["test.docx"].metainfo.thumbnail
    assert b"\x89PNG" in processed_X["test.pdf"].metainfo.thumbnail
