from string import punctuation
from unstructured.cleaners import core as cleaners_core


def clean_chunk(text):
    # do simple prepeocessing of extracted text from chunk
    text = cleaners_core.clean_non_ascii_chars(text)
    text = cleaners_core.clean(text, extra_whitespace=True,
                               dashes=True, bullets=True,
                               trailing_punctuation=False)
    # remove punctuation from the beginning of the word
    text = text.lstrip(punctuation)
    return text
