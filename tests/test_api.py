import base64
import json
import os

import pytest
import requests


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


@pytest.fixture
def base_api_url():
    return "http://127.0.0.1:8012"


def test_api_thumbnails_llm_summary_pdf(sample_pdf_path, base_api_url):
    url = f"{base_api_url}/process_files_by_stream"
    headers = {"accept": "application/json"}
    with open(sample_pdf_path, "rb") as f:
        files = {"pdfs": (os.path.basename(sample_pdf_path), f.read(), "application/pdf")}
    data = {
        "text_extractor": "unstructured",
        "meta_extractor": "dummy",
        "chunker": "standard",
        "thumbnails": True,
        "llm_summary": True,
        "llm_table_description": False,
        "llm_model": "llama-3.2-3b-preview",
        "llm_provider": "groq",
    }
    data = {"params": json.dumps(data)}

    # Send the POST request
    response = requests.post(url, headers=headers, files=files, data=data)

    # Assertions to check the response status and content
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.headers["Content-Type"] == "application/json", "Response is not JSON"
    response_json = response.json()

    doc = response_json["extracted"][0]
    assert all([kwd in doc["metainfo"]["abstract"] for kwd in ["Transformer", "attention"]])

    png = base64.b64decode(doc["metainfo"]["thumbnail"])
    assert png.startswith(b"\x89PNG\r\n\x1a\n"), "Thumbnail is not a PNG image"
    assert "Each layer has two sub layers" in doc["chunks"][10]["text"]
    assert doc["metainfo"]["file_features"]["filename"] == os.path.basename(sample_pdf_path)


def test_api_thumbnails_llm_summary_doc_german(sample_doc_german_path, base_api_url):
    url = f"{base_api_url}/process_files_by_stream"
    headers = {"accept": "application/json"}
    with open(sample_doc_german_path, "rb") as f:
        files = {"pdfs": (os.path.basename(sample_doc_german_path), f.read(), "application/msword")}
    data = {
        "text_extractor": "unstructured",
        "meta_extractor": "dummy",
        "chunker": "standard",
        "thumbnails": True,
        "llm_summary": True,
        "llm_table_description": False,
        "llm_model": "llama-3.2-3b-preview",
        "llm_provider": "groq",
    }
    data = {"params": json.dumps(data)}

    # Send the POST request
    response = requests.post(url, headers=headers, files=files, data=data)

    # Assertions to check the response status and content
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.headers["Content-Type"] == "application/json", "Response is not JSON"
    response_json = response.json()

    doc = response_json["extracted"][0]
    assert all([kwd in doc["metainfo"]["abstract"] for kwd in ["Sierra Leone", "Konflikt"]])

    png = base64.b64decode(doc["metainfo"]["thumbnail"])
    assert png.startswith(b"\x89PNG\r\n\x1a\n"), "Thumbnail is not a PNG image"
    assert "Das Zertifikationssystem ist im Grunde eine Regelung" in doc["chunks"][10]["text"]
    assert doc["metainfo"]["file_features"]["filename"] == os.path.basename(sample_doc_german_path)
