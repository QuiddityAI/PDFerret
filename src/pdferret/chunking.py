from dataclasses import asdict

import numpy as np
from nltk.tokenize import sent_tokenize

from .base import BaseProcessor
from .cleaning import clean_chunk
from .datamodels import PDFChunk, PDFDoc
from .utils.metrics import spellcheck_score

LIMITS_SOFT = 700, 1200
LIMITS_HARD = 400, 1600
MIN_CHUNK_LEN = 50
SPELLCHECK_SCORE_THRESHOLD = 0.5


def partition_list(a, k):
    # split a list of numbers into sublists such that sum in every sublist is approx equal
    # from https://stackoverflow.com/questions/35517051/split-a-list-of-numbers-into-n-chunks-such-that-the-chunks-have-close-to-equal
    if k <= 1:
        return [a]
    if k >= len(a):
        return [[x] for x in a]
    partition_between = [(i + 1) * len(a) // k for i in range(k - 1)]
    average_height = float(sum(a)) / k
    best_score = None
    best_partitions = None
    count = 0

    while True:
        starts = [0] + partition_between
        ends = partition_between + [len(a)]
        partitions = [a[starts[i] : ends[i]] for i in range(k)]
        heights = list(map(sum, partitions))

        abs_height_diffs = list(map(lambda x: abs(average_height - x), heights))
        worst_partition_index = abs_height_diffs.index(max(abs_height_diffs))
        worst_height_diff = average_height - heights[worst_partition_index]

        if best_score is None or abs(worst_height_diff) < best_score:
            best_score = abs(worst_height_diff)
            best_partitions = partitions
            no_improvements_count = 0
        else:
            no_improvements_count += 1

        if worst_height_diff == 0 or no_improvements_count > 5 or count > 100:
            return best_partitions
        count += 1

        move = -1 if worst_height_diff < 0 else 1
        bound_to_move = (
            0
            if worst_partition_index == 0
            else (
                k - 2
                if worst_partition_index == k - 1
                else (
                    worst_partition_index - 1
                    if (worst_height_diff < 0)
                    ^ (heights[worst_partition_index - 1] > heights[worst_partition_index + 1])
                    else worst_partition_index
                )
            )
        )
        direction = -1 if bound_to_move < worst_partition_index else 1
        partition_between[bound_to_move] += move * direction


def split_chunk(chunk):
    # optimally split single chunk into multiple smaller chunks
    # respect sentences
    # TODO: prefix and suffix are not handled
    sentences = sent_tokenize(chunk.text)
    lens = [len(s) for s in sentences]
    total_len = len(chunk.text)
    max_split = int(np.ceil(total_len / LIMITS_SOFT[0]))
    min_split = np.ceil(total_len / LIMITS_SOFT[1])
    min_split = int(np.maximum(min_split, 2))
    # iterate over probable range of splits
    for n_splits in range(min_split, max_split + 1):
        sublists = partition_list(lens, n_splits)
        if all([sum(s) for s in sublists]) < LIMITS_HARD[1]:
            break

    new_chunks_texts = []
    start = 0
    for sublist in sublists:
        end = len(sublist) + start
        new_chunks_texts.append(" ".join(sentences[start:end]))
        start = end

    coord_ratios = np.cumsum([sum(s) / total_len for s in sublists])[:-1]
    new_coordinates = split_coordinates(chunk.coordinates, coord_ratios)

    new_chunks = []
    for new_text, new_coords in zip(new_chunks_texts, new_coordinates):
        new_chunk = PDFChunk(**asdict(chunk))
        new_chunk.coordinates = new_coords
        new_chunk.text = new_text
        new_chunks.append(new_chunk)

    return new_chunks


def split_coordinates(coordinates, ratios):
    # ratios: list of relative borders to split at,
    # e.g. [0.5] to split 50:50, [0.2, 0.5] to split into
    # 0.2, 0.3, 0.5 and so on
    # assume that we can always split chunk vertically
    if not coordinates:
        return []
    (xmin, ymin), (xmax, ymax) = coordinates
    height = ymax - ymin

    coords = []
    block_start = 0
    for ratio in list(ratios) + [1.0]:

        block_end = ratio + block_start

        c = [(xmin, ymin + block_start * height), (xmax, ymin + (block_end - block_start) * height)]

        coords.append(c)
        block_start = block_end - block_start

    return coords


def combine_chunks(chunk, chunks):
    # optimally combine current chunk with others
    tot_len = len(chunk.text)
    chunks_to_take = 0

    # find how many chunks we need to combine
    for candidate in chunks:
        tot_len += len(candidate.text)
        chunks_to_take += 1
        if tot_len > LIMITS_SOFT[0]:
            break
    for i in range(chunks_to_take):
        new_chunk = chunks.pop(0)
        chunk.text += " " + new_chunk.text
        # only enlarge bbox if they're on the same page
        if chunk.page == new_chunk.page and chunk.coordinates:
            chunk.coordinates = combine_coordinates(chunk.coordinates, new_chunk.coordinates)

    return chunk


def combine_coordinates(a, b):
    xmin = np.minimum(a[0][0], b[0][0])
    ymin = np.minimum(a[0][1], b[0][1])
    xmax = np.maximum(a[1][0], b[1][0])
    ymax = np.maximum(a[1][1], b[1][1])
    return [(xmin, ymin), (xmax, ymax)]


def combine_two_chunks(chunk1, chunk2):
    # combine current two chunks taking into account their coordinates
    chunk = PDFChunk(**asdict(chunk1))
    chunk.text = chunk1.text + " " + chunk2.text
    # only enlarge bbox if they're on the same page
    if chunk1.page == chunk2.page and chunk1.coordinates and chunk2.coordinates:
        chunk.coordinates = combine_coordinates(chunk1.coordinates, chunk2.coordinates)
    return chunk


def concatenate_chunks(chunks, A, B):
    def can_concatenate(s1, s2, A, B):
        return len(s1.text) + len(s2.text) <= B and len(s1.text) < A and len(s2.text) < A

    result = []
    i = 0
    while i < len(chunks):
        current_chunk = chunks[i]
        j = i - 1
        while j >= 0 and can_concatenate(chunks[j], current_chunk, A, B):
            current_chunk = combine_two_chunks(chunks[j], current_chunk)
            j -= 1

        j = i + 1
        while j < len(chunks) and can_concatenate(current_chunk, chunks[j], A, B):
            current_chunk = combine_two_chunks(current_chunk, chunks[j])
            j += 1

        result.append(current_chunk)
        i = j

    return result


def chunk_filter(text, lang):
    if len(text) < MIN_CHUNK_LEN:
        return False
    if spellcheck_score(text, lang) < SPELLCHECK_SCORE_THRESHOLD:
        return False
    return True


class StandardChunker(BaseProcessor):
    parallel = False
    operates_on = PDFDoc

    def __init__(self, clean_text=True):
        self.clean_text = clean_text

    def process_single(self, doc: PDFDoc) -> PDFDoc:
        # First pass: split all large chunks into smaller ones:
        shorter_chunks = []
        for ch in doc.chunks:
            if ch.locked:
                shorter_chunks.append(ch)
                continue
            if len(ch.text) > LIMITS_SOFT[1]:
                shorter_chunks.extend(split_chunk(ch))
            else:
                shorter_chunks.append(ch)

        # Second pass: remove bad chunks
        filtered_chunks = [
            ch for ch in shorter_chunks if chunk_filter(ch.text, lang=doc.metainfo.language) or ch.locked
        ]
        # remove locked chunks, i.e. those which can't be concatenated with others
        non_locked_chunks = [ch for ch in filtered_chunks if not ch.locked]
        locked_chunks = [ch for ch in filtered_chunks if ch.locked]
        # third pass: combine short chunks into longer ones
        normal_len_chunks = concatenate_chunks(non_locked_chunks, LIMITS_SOFT[0], LIMITS_HARD[1])
        normal_len_chunks += locked_chunks
        # fourth pass: clean the text
        if self.clean_text:
            final_chunks = []
            for ch in normal_len_chunks:
                ch.text = clean_chunk(ch.text, doc.metainfo.language) if not ch.locked else ch.text
                final_chunks.append(ch)
            doc.chunks = final_chunks
        else:
            doc.chunks = normal_len_chunks

        return doc
