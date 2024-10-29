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


def test_extraction_via_api(
    sample_doc_german_path,
    sample_doc_path,
    sample_docx_path,
    sample_docx_w_table_path,
    sample_pdf_path,
    sample_pptx_path,
    base_api_url,
):
    url = f"{base_api_url}/process_files_by_stream"
    headers = {"accept": "application/json"}
    file_paths = [
        sample_doc_german_path,
        sample_doc_path,
        sample_docx_path,
        sample_docx_w_table_path,
        sample_pdf_path,
        sample_pptx_path,
    ]
    files = []
    for fpath in file_paths:
        files.append(("pdfs", (os.path.basename(fpath), open(fpath, "rb"), "application/pdf")))
    params = {
        "vision_model": "Mistral_Pixtral",
        "text_model": "Nebius_Llama_3_1_70B_fast",
        "lang": "en",
        "return_images": True,
        "perfile_settings": {
            os.path.basename(sample_doc_german_path): {"lang": "de"},
            os.path.basename(sample_doc_path): {
                "lang": "en",
                "extra_metainfo": {"Author information": "John Doe"},
            },
        },
    }
    data = {"params": json.dumps(params)}

    # Send the POST request
    response = requests.post(url, headers=headers, files=files, data=data)

    # Assertions to check the response status and content
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert response.headers["Content-Type"] == "application/json", "Response is not JSON"
    response_json = response.json()

    docs = response_json["extracted"]
    errors = response_json["errors"]
    assert len(docs) == len(file_paths), f"Expected {len(file_paths)} documents, got {len(docs)}"
    assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}"
    for doc in docs:
        assert "metainfo" in doc, "Expected 'metainfo' key in document"
        assert "chunks" in doc, "Expected 'chunks' key in document"
        metainfo = doc["metainfo"]
        chunks = doc["chunks"]
        assert len(chunks) > 0, "Expected at least one chunk in the document"
        assert "title" in metainfo, "Expected 'title' key in metainfo"
        assert metainfo["title"], "Expected 'title' to be non-empty"

    assert docs[0]["metainfo"]["language"] == "de", "Expected German language for the first document"
    assert docs[1]["metainfo"]["authors"] == ["John Doe"], "Expected author information for the second document"
