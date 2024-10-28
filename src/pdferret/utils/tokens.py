import re


def count_tokens_rough(text):
    # Split the text based on whitespace and common code symbols
    tokens = re.split(r"\s+|[()\[\]{}.,:;+=*/\\\"\'<>-]", text)
    # Filter out any empty strings resulting from the split
    tokens = [token for token in tokens if token]
    return len(tokens)
