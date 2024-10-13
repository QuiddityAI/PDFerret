import os
import subprocess
import tempfile
from typing import Dict

from ..base import BaseProcessor
from ..datamodels import PDFDoc, PDFError


def run_command(command):
    """
    Run a shell command and return the output, error and return code.

    :param command: Command to be executed as a string.
    :return: A tuple containing (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout, result.stderr, result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode


def make_thumbnail_libreoffice(files: list[str], output_dir: str):
    """
    Convert a list of files to thumbnails using LibreOffice.

    :param files: List of file paths to be converted.
    :param output_dir: Directory where the thumbnails will be saved.
    """
    command = ["libreoffice", "--convert-to", "png", "--outdir", output_dir, *files]
    stdout, stderr, return_code = run_command(command)
    return stdout, stderr


class LibreOfficeThumbnailer(BaseProcessor):
    parallel = False
    operates_on = PDFDoc

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        # just dummy, actual processing is in _process_batch
        return doc

    def _process_batch(self, X: Dict[str, PDFDoc]) -> tuple[Dict[str, PDFDoc], Dict[str, PDFError]]:
        with tempfile.TemporaryDirectory() as output_dir:
            stdout, stderr = make_thumbnail_libreoffice(
                [doc.metainfo.file_features.file for doc in X.values()], output_dir
            )
            for doc in X.values():
                base_name = os.path.basename(doc.metainfo.file_features.file)
                name, _ = os.path.splitext(base_name)
                thumbnail_path = os.path.join(output_dir, f"{name}.png")
                try:
                    with open(thumbnail_path, "rb") as f:
                        doc.metainfo.thumbnail = f.read()
                except FileNotFoundError:
                    pass
        return X, {}
