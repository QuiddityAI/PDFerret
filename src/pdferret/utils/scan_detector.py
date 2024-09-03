import numpy as np
from pypdf import PdfReader


def gen_dict_extract(key, var):
    if hasattr(var, "items"):
        for k, v in var.items():
            v = v.get_object()
            if k == key:
                for k2, v2 in v.items():
                    v2 = v2.get_object()
                    if v2.get("/Subtype") == "/Image":
                        yield v2
            if hasattr(v, "items"):
                for result in gen_dict_extract(key, v):
                    yield result


def extract_img_sizes(reader):
    # iterate through pdf metainformation until XObject of type image is found
    # and extract its width and height relative to page size
    sizes = []
    for page in reader.pages:
        obj = page.get_object()
        for val_obj in gen_dict_extract("/XObject", obj["/Resources"]):
            h, w = val_obj["/Height"], val_obj["/Width"]
            sizes.append((h / page.mediabox.height, w / page.mediabox.width))
    return np.array(sizes)


def mad(x):
    return np.median(np.abs(x - np.median(x, axis=0)))


def is_scanned(reader: PdfReader):
    number_of_pages = len(reader.pages)
    # firsly we extract metainformation about images in PDF file
    sizes = extract_img_sizes(reader)
    # in scanned PDF number of pages is same
    # as number of images
    if number_of_pages != len(sizes):
        return False
    # if it's scanned, majority of images must be bigger then mediabox
    if np.median(sizes >= 1) < 1:
        return False
    # finally check that majority of images has same size:
    if mad(sizes) > 0.1:
        return False
    return True
