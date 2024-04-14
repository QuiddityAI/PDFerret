import numpy as np
from ..base import BaseProcessor
from ..datamodels import PDFChunk, MetaInfo, PDFDoc
from unstructured.partition.pdf import partition_pdf
from unstructured.documents import elements as doc_elements


def extract_bbox(coords):
    coords = np.array(coords)
    xmin = coords[:, 0].min()
    xmax = coords[:, 0].max()
    # looks like ther're discrepancy in definining
    # direction of y-axis, some define it pointing up
    # some pointing down
    # according to Apache PDFBox (https://pdfbox.apache.org/download.html)
    # it should be defined pointing up, which is assumed here
    ymax = 1 - coords[:, 1].min()
    ymin = 1 - coords[:, 1].max()
    return (xmin, xmax, ymin, ymax)


class UnstructuredTextExtractor(BaseProcessor):
    parallel = "process"
    operates_on = MetaInfo

    def __init__(self, strategy="auto", languages=('eng',), min_text_len=20, batch_size=16, n_proc=8):
        '''
        strategy, languages - passed to unstructured partition_pdf
        min_text_len - text elements smaller then this size will be dropped
        '''
        super().__init__(n_proc=n_proc, batch_size=batch_size)
        self.strategy = strategy
        self.languages = list(languages)
        self.min_text_len = min_text_len

    def process_single(self, meta: MetaInfo) -> PDFDoc:
        pdf = meta.file_features.file
        if isinstance(pdf, str):
            input_kwargs = dict(filename=pdf)
        else:
            input_kwargs = dict(file=pdf)

        elements = partition_pdf(**input_kwargs, strategy=self.strategy,
                                 languages=self.languages)

        chunks = []
        for el in elements:
            if not isinstance(el, (doc_elements.NarrativeText, doc_elements.Text)):
                continue

            eldict = el.to_dict()
            text = eldict['text']
            if len(text) < self.min_text_len:
                continue

            coords = eldict['metadata']['coordinates']
            norm_coords = [(p[0] / coords['layout_width'],
                            p[1] / coords['layout_height']) for p in coords['points']]

            xmin, xmax, ymin, ymax = extract_bbox(norm_coords)

            chunk = PDFChunk(page=eldict['metadata']['page_number'],
                             text=text,
                             coordinates=[(xmin, ymin), (xmax, ymax)])
            chunks.append(chunk)
        return PDFDoc(metainfo=meta, chunks=chunks)
