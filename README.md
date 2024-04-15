# PDFerret

pdferret - an aggregator for multiple PDF information extractors

# Installation

1. To install the package, use `pip install .` in the source folder, which will install package with all dependencies
2. On minimal Ubuntu systems (e.g. in a python Docker image), `sudo apt install libgl1` might be needed for opencv
3. PDFerret relies on GROBID for extracting some parts of the text. Run `docker compose -f docker-compose-grobid.yml up` to run GROBID server. `docker-compose-grobid-big.yml` contains GROBID with ML models, thus produces much bigger image and significantly slower, while improvements are not so clear.
4. If running in Docker, you can set GROBID url via environment variable `PDFERRET_GROBID_URL`

# Usage

As soon as pdferret package is installed and GROBID is running you can import the package and parse the batch of PDFs:

```python
from pdferret import PDFerret

# instantiate it like this:
# for now only text_extractor supports two options, either "grobid" or "unstructured"
extractor = PDFerret(text_extractor="unstructured")

extracted, errors = extractor.extract_batch(list_of_pdf_files)
```

# Example

see `demo_pdferret.ipynb` for example of usage.
