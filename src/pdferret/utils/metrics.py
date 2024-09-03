import numpy as np
from nltk import word_tokenize, wordpunct_tokenize
from spellchecker import SpellChecker

from .langdetect import lang_codes

dictionaries = {lang: SpellChecker(lang).word_frequency.dictionary for lang in lang_codes}

lang_code_to_nltk = {"en": "english", "fr": "french", "de": "german"}


def spellcheck_score(text: str, lang: str):
    words = [w.lower() for w in word_tokenize(text, language=lang_code_to_nltk[lang]) if len(w) > 3]
    if not words:
        return 0.0
    correct_words = sum([w in dictionaries[lang] for w in words])
    return correct_words / len(words)


def wordlen_score(text: str, lang: str):
    wordlens = [len(w) for w in word_tokenize(text, language=lang_code_to_nltk[lang])]
    return np.average(wordlens), np.std(wordlens)
