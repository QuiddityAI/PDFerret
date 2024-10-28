import os
import shutil
import tempfile
from typing import Dict

from ..base import BaseProcessor
from ..datamodels import PDFDoc, PDFError
from ..utils.shell_run import run_command


def convert_libreoffice(files: list[str], output_dir: str, output_format: str = "odt"):
    """
    Convert a list of files to thumbnails using LibreOffice.

    :param files: List of file paths to be converted.
    :param output_dir: Directory where the thumbnails will be saved.
    """
    command = ["libreoffice", "--convert-to", output_format, "--outdir", output_dir, *files]
    stdout, stderr, return_code = run_command(command)
    return stdout, stderr


class LibreOfficeConverter(BaseProcessor):
    operates_on = PDFDoc
    parallel = False

    def __init__(self, target_format="odt", n_proc=None, batch_size=None):
        super().__init__(n_proc, batch_size)
        self.target_format = target_format

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        # just dummy, actual processing is in _process_batch
        return doc

    def _process_batch(self, X: Dict[str, PDFDoc]) -> tuple[Dict[str, PDFDoc], Dict[str, PDFError]]:
        with tempfile.TemporaryDirectory() as output_dir:
            stdout, stderr = convert_libreoffice(
                [doc.metainfo.file_features.file for doc in X.values()], output_dir, self.target_format
            )
            errors = {}
            results = {}
            for key, doc in X.items():
                try:
                    base_name = os.path.basename(doc.metainfo.file_features.file)
                    name, _ = os.path.splitext(base_name)
                    converted_path = os.path.join(output_dir, f"{name}.{self.target_format}")
                    # copy converted file to the original file path
                    new_path = os.path.join(
                        os.path.dirname(doc.metainfo.file_features.file), f"{name}.{self.target_format}"
                    )
                    shutil.copy(converted_path, new_path)
                except Exception as e:
                    errors[key] = PDFError(repr(e), file=key, traceback=stderr)
                    continue
                doc.metainfo.file_features.file = new_path
                results[key] = doc
        return results, errors
