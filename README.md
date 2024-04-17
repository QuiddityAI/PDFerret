# PDFerret

pdferret - an aggregator for multiple PDF information extractors

# Installation

1. To install the package, use `pip install .` in the source folder, which will install package with all dependencies
2. On minimal Ubuntu systems (e.g. in a python Docker image), `sudo apt install libgl1` might be needed for opencv
3. PDFerret relies on GROBID for extracting some parts of the text. Run `docker compose -f docker-compose-grobid.yml up` to run GROBID server. `docker-compose-grobid-big.yml` contains GROBID with ML models, thus produces much bigger image and significantly slower, while improvements are not so clear.

# Configuration

Following env variables are supported to configure PDFerret:
- `PDFERRET_GROBID_URL` - sets url of GROBID, used by extractors
- `PDFERRET_NPROC` - sets number of processors used for parallel processing for both metainfo and text extractors
- `PDFERRET_BATCH_SIZE` - sets batch size for parallel processing, i.e. how many items are processed between fork and join. Must be at least `PDFERRET_NPROC`, but shouldn't have strong influence on performance otherwise


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
