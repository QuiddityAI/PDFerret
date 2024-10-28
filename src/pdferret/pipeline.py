from typing import List

from .base import BaseProcessor
from .datamodels import FileFeatures, MetaInfo, PDFDoc, PDFError, PDFFile


class Pipeline:
    def __init__(self, steps: List[BaseProcessor]):
        self.steps = steps

    def extract_batch(self, pdfdocs: List[PDFDoc]) -> tuple[List[PDFDoc], List[PDFError]]:
        errors = {}
        # run the pipeline steps on pdfdocs
        for step in self.steps:
            print(f"Running step {step.__class__.__name__}")
            pdfdocs, step_errors = step.process_batch(pdfdocs)
            errors.update(step_errors)

        return pdfdocs, errors
