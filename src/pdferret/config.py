import multiprocessing
import os
from .logging import logger

NPROC = multiprocessing.cpu_count()
if nproc_env := os.environ.get("PDFERRET_NPROC"):
    NPROC = int(nproc_env.strip())


BATCH_SIZE = 2*NPROC
if bsize_env := os.environ.get("PDFERRET_BATCH_SIZE"):
    BATCH_SIZE = int(bsize_env.strip())

logger.info(
    f"Using {NPROC} CPUs and {BATCH_SIZE} batch size")

GROBID_URL = "http://localhost:8070"
if url_env := os.environ.get("PDFERRET_GROBID_URL"):
    GROBID_URL = url_env

MAX_PAGES = 30
if maxpages_env := os.environ.get("PDFERRET_MAX_PAGES"):
    MAX_PAGES = maxpages_env
