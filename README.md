# PDFerret v2

pdferret v2 - a general information extraction library with connectors to different formats

# Installation

1. To install the package, use `pip install .` in the source folder, which will install package with all dependencies
2. On minimal Ubuntu systems (e.g. in a python Docker image), `sudo apt install libgl1` might be needed for opencv
3. PDFerret relies on Tika for processing general documents. This requries up to date Tika (tested on apache/tika:3.0.0.0-BETA2-full) up and running on localhost:9998. You can overwrite tika server address by setting env var `PDFERRET_TIKA_SERVER_URL`.
Please note that python tika package used as a client in this lib can download and run it's own version of Tika if the server is not found, which can lead to unpredictable results. In this case it might help to set `TIKA_CLIENT_ONLY=1` in docker-compose file.

# Configuration

Following env variables are supported to configure PDFerret:
- `PDFERRET_GROBID_URL` - sets url of GROBID, used by extractors
- `PDFERRET_NPROC` - sets number of processors used for parallel processing for both metainfo and text extractors
- `PDFERRET_BATCH_SIZE` - sets batch size for parallel processing, i.e. how many items are processed between fork and join. Must be at least `PDFERRET_NPROC`, but shouldn't have strong influence on performance otherwise
- `PDFERRET_MAX_PAGES` - all pdfs will be cropped to first MAX_PAGES WARNING! Currently not implemented
- `PDFERRET_TIKA_SERVER_URL` - address of the Tika
- `PDFERRET_TIKA_OCR_STRATEGY` - controls how Tika will handle pdfs without text. Must be one of 'AUTO', 'OCR_ONLY', 'NO_OCR', 'OCR_AND_TEXT_EXTRACTION', defaults to 'NO_OCR'
- `PDFERRET_VISUAL_MAX_PAGES` - sets how many pages will be used for extracting information with vision model. Defaults to 3.
- LLMonkey API keys are also required for some extractors, see llmonkey documentation for more information
- `PDFERRET_MAX_CHUNK_LEN` - maximum length of chunk for chunking algo
- `PDFERRET_CHUNK_OVERLAP` - overlap of chunks for chunking algo

## Using the Google API

Create a credentials file before building the Docker container using:
`gcloud auth application-default login`

It will then be mounted to the container.

# Usage

As soon as pdferret package is installed and GROBID is running you can import the package and parse the batch of PDFs:

```python
from pdferret import PDFerret
from llmonkey.llms import

extractor = PDFerret()
files = ["file1.pdf", "file2.xlsx", "file3.docx"] # list of file paths
# v2 only supports files passed as list of paths
extracted, errors = extractor.extract_batch(files, lang="en")
# lang argument is optional, but highly recommended, it improves the quality of the results
# a lot for non-english documents
```

# API usage

Run `docker compose up` to build the container. Warning: it will download Tika image, which is ~ 1GB.

Warning: client.py is not yet updated to v2, so it will not work with the current version of the server. Instead, see
tests/test_api.py for example of usage.

# Development
Probably the most important part to update is the recipes in `pdferret/recipes`. They define how to extract information from different types of documents. Optionally, a new processors can be created, subclassing `pdferret.base.BaseProcessor` and implementing `process_single` method. The `process_single` method will be parallelized depending on the `parallel` attribute of the processor, which can be set to `thread`, `process` or `none`. Alternatively, if different parallelization is needed, the `_process_batch` method can be implemented.

# Testing

Most of the tests are not yet updated to v2, so they will not work with the current version of the library. However, the tests in `tests/test_api.py` should work. To run them, use `pytest tests/test_api.py`.

# Deprecated code

Library still contains a lot of not used code from the previous version, including Grobid and Unstructured extractors.
They are not used in the current version of the library and probably should be removed in the future.
