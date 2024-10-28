import glob
import json
from dataclasses import asdict

from llmonkey.llms import Mistral_Pixtral, Nebius_Llama_3_1_70B_fast

from .datamodels import ChunkType, PDFDoc
from .pdferret import PDFerret


def clean_pdfdoc_to_dict(pdfdoc: PDFDoc) -> dict:
    pdfdoc.metainfo.file_features = None
    pdfdoc.metainfo.thumbnail = None
    pdfdoc.metainfo.extra_metainfo = None
    for chunk in pdfdoc.chunks:
        chunk.non_embeddable_content = None
        chunk.chunk_type = chunk.chunk_type.value
    return asdict(pdfdoc)


if __name__ == "__main__":

    pdferret = PDFerret(text_model=Nebius_Llama_3_1_70B_fast(), vision_model=Mistral_Pixtral())

    files = glob.glob("/home/andre/Documents/projects/pdferret/test_data/Literatur/Neuroscience medical imaging/*.pdf")

    pdfdocs, errors = pdferret.extract_batch(files[:20], lang="en")
    for pdfdoc in pdfdocs:
        print(pdfdoc.metainfo)
        fname = pdfdoc.metainfo.file_features.filename
        # change extension to json
        fname = fname[: fname.rfind(".")] + ".json"
        with open(fname, "w") as f:
            json.dump(clean_pdfdoc_to_dict(pdfdoc), f, indent=4)
    print(errors)
