from abc import ABC, abstractmethod
from typing import BinaryIO, List, Union, Dict
import concurrent.futures
from .utils import split_every
from .datamodels import PDFDoc
import logging

engines = {"thread": concurrent.futures.ThreadPoolExecutor,
           "process": concurrent.futures.ProcessPoolExecutor}


class BaseExtractor(ABC):
    parallel = False

    def __init__(self, n_proc=None, batch_size=None) -> None:
        self.n_proc = n_proc
        self.batch_size = batch_size

    @abstractmethod
    def extract_single(self, pdf: Union[str, BinaryIO]):
        pass

    def extract_batch(self, X: Dict[str, Union[str, BinaryIO]]):
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
                              pdfs: Dict[str, Union[str, BinaryIO]]):
        parsed_batch = {}
        for _id, pdf in pdfs.items():
            try:
                ext = self.extract_single(pdf)
                parsed_batch[_id] = ext
            except Exception as e:
                logging.warning(f"{_id} failed: {repr(e)}")

        return parsed_batch

    def _process_batch_parallel(self,
                                pdfs: Dict[str, Union[str, BinaryIO]]):
        parsed_batch = {}
        Engine = engines[self.parallel]
        with Engine(max_workers=self.n_proc) as executor:
            results = []
            for _id, pdf in pdfs.items():
                r = executor.submit(self.extract_single, pdf)
                r._id = _id
                results.append(r)

        for r in concurrent.futures.as_completed(results):
            if r.exception():
                logging.warning(f"{r._id} failed: {repr(r.exception())}")
                continue
            parsed = r.result()
            parsed_batch[r._id] = parsed

        return parsed_batch


class BaseProcessor(BaseExtractor):
    parallel = False

    def extract_single(self, inp):
        return self.process_single(inp)
    
    def process_batch(self, X: List[PDFDoc]):
        return super().extract_batch(X)
    
    @abstractmethod
    def process_single(self, doc: PDFDoc) -> PDFDoc:
        pass
    