from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, get_args
import concurrent.futures
from .utils.utils import split_every
from .datamodels import PDFDoc, PDFChunk, MetaInfo, PDFFile
import logging

engines = {"thread": concurrent.futures.ThreadPoolExecutor,
           "process": concurrent.futures.ProcessPoolExecutor}


class Parallelizable(ABC):
    """Base implementing parallel processing and batching

    """

    parallel = False

    def __init__(self, n_proc=None, batch_size=None) -> None:
        self.n_proc = n_proc
        self.batch_size = batch_size

    @abstractmethod
    def _process_single(self, pdf: PDFFile):
        pass

    def _process_batch(self, X: Dict[str, PDFFile]):
        parsed = {}
        if not self.parallel:
            parsed = self._process_serial(X)
        else:
            for batch_keys in split_every(X, self.batch_size):
                batch = {k: X[k] for k in batch_keys}
                p = self._process_batch_parallel(batch)    
                parsed.update(p)
        return parsed

    def _process_serial(self,
                              pdfs: Dict[str, PDFFile]):
        parsed_batch = {}
        for _id, pdf in pdfs.items():
            try:
                ext = self._process_single(pdf)
                parsed_batch[_id] = ext
            except Exception as e:
                logging.warning(f"{_id} failed: {repr(e)}")

        return parsed_batch

    def _process_batch_parallel(self,
                                pdfs: Dict[str, PDFFile]):
        parsed_batch = {}
        Engine = engines[self.parallel]
        with Engine(max_workers=self.n_proc) as executor:
            results = []
            for _id, pdf in pdfs.items():
                r = executor.submit(self._process_single, pdf)
                r._id = _id
                results.append(r)

        for r in concurrent.futures.as_completed(results):
            if r.exception():
                logging.warning(f"{r._id} failed: {repr(r.exception())}")
                continue
            parsed = r.result()
            parsed_batch[r._id] = parsed

        return parsed_batch
    



class BaseProcessor(Parallelizable):
    """Base class that operates on pdfs or extracted data"""

    parallel = False
    operates_on = int # one of PDFDoc, MetaInfo, Chunk, PDFFile

    def _process_single(self, inp):
        # isinstance can't simply check against Union type, 
        # need to wrap it in get_args
        if isinstance(inp, self.operates_on):
            return self.process_single(inp)
        else:
            raise TypeError(f"This class operates on {self.operates_on} type but {type(inp)} is given")
    
    def process_batch(self, X):
        return super()._process_batch(X)
    
    @abstractmethod
    def process_single(self, X: PDFDoc | PDFChunk | MetaInfo | PDFFile) -> PDFDoc | PDFChunk | MetaInfo:
        pass
    