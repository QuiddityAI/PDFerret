from spellchecker import SpellChecker
from nltk import wordpunct_tokenize, word_tokenize
import numpy as np

dictionary = SpellChecker().word_frequency.dictionary


def spellcheck_score(text):
    words = [w.lower() for w in wordpunct_tokenize(text) if len(w) > 3]
    if not words:
        return 0.0
    correct_words = sum([w in dictionary for w in words])
    return correct_words / len(words)


def wordlen_score(text):
    wordlens = [len(w) for w in word_tokenize(text)]
    return np.average(wordlens), np.std(wordlens)
