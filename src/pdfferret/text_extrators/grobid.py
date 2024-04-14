import io
from typing import BinaryIO, List, Union

import numpy as np
from pypdf import PdfReader, PdfWriter
from .. import scipdf
from ..base import BaseProcessor
from ..datamodels import MetaInfo, PDFChunk, PDFDoc


def most_common(lst):
    return max(set(lst), key=lst.count)


def combine_bboxes(coords):
    # extract global bounding box by combining all smaller bboxes
    bboxes = []
    for bbox in coords:
        bboxes.append([float(b) for b in bbox[1:]])

    bboxes = np.array(bboxes)
    # make absolute coordinates form h, w
    bboxes[:, 2] += bboxes[:, 0]
    bboxes[:, 3] += bboxes[:, 1]

    xmin = bboxes[:, 0].min()
    ymin = bboxes[:, 1].min()
    xmax = bboxes[:, 2].max()
    ymax = bboxes[:, 3].max()
    return (xmin, ymin, xmax, ymax)


class GROBIDTextExtractor(BaseProcessor):
    parallel = False  # "thread"
    operates_on = MetaInfo

    def __init__(self, extract_meta=False, max_pages=30, grobid_url="http://localhost:8070", batch_size=16, n_proc=8):
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.grobid_url = grobid_url
        self.extract_meta = extract_meta
        self.max_pages = max_pages

    def _extract_chunks(self, parsed) -> List[PDFChunk]:
        chunks = []
        for section in parsed['sections']:
            for text in section['text']:
                coords = text.get('coords')
                page = None
                if coords:
                    pages = [c[0] for c in coords]
                    page = most_common(pages)
                    if len(set(pages)) > 1:
                        coords = [c for c in coords if c[0] == page]
                    xmin, ymin, xmax, ymax = combine_bboxes(coords)
                    page_sizes = {p['n']: p for p in parsed['page_sizes']}
                    page_size = page_sizes[page]
                    page_width = float(
                        page_size['lrx']) - float(page_size['ulx'])
                    page_height = float(
                        page_size['lry']) - float(page_size['uly'])

                    xmin_r = (xmin - float(page_size['ulx'])) / page_width
                    xmax_r = (xmax - float(page_size['ulx'])) / page_width
                    # see unstructured.py for explanation about y-axis inversion
                    ymax_r = 1.0 - \
                        (ymin - float(page_size['uly'])) / page_height
                    ymin_r = 1.0 - \
                        (ymax - float(page_size['uly'])) / page_height
                    coordinates = [(xmin_r, ymin_r), (xmax_r, ymax_r)]
                else:
                    coordinates = []

                chunk = dict(
                    text=text['text'],
                    page=int(page) if page is not None else None,
                    coordinates=coordinates)
                chunks.append(PDFChunk(**chunk))
        return chunks

    def process_single(self, meta: MetaInfo) -> PDFDoc:
        pdf = meta.file_features.file
        # this will work for both filepath and BinaryIO
        if meta.npages > self.max_pages:
            reader = PdfReader(meta.file_features.file)
            buff = io.BytesIO()
            writer = PdfWriter()
            for i in range(self.max_pages):
                writer.add_page(reader.pages[i])
            writer.write(buff)
            parsed = scipdf.parse_pdf_to_dict(
                buff.getvalue(), grobid_url=self.grobid_url)

        # special case for npages < max_pages and being BinaryIO
        # unfortuntely there's no good way to check if something
        # is file-like object
        elif not isinstance(pdf, str):
            parsed = scipdf.parse_pdf_to_dict(
                pdf.getvalue(), grobid_url=self.grobid_url)
        else:
            parsed = scipdf.parse_pdf_to_dict(pdf, grobid_url=self.grobid_url)
        if self.extract_meta:
            meta.doi = parsed['doi']
            meta.title = parsed['title']
            meta.authors = parsed['authors']
            meta.pub_date = parsed['pub_date']
            meta.abstract = parsed['abstract']

        chunks = self._extract_chunks(parsed)
        return PDFDoc(meta, chunks)
