"""Payload generator module.

This module contains functionality to create synonyms (which form the
basis of IPMs) and subsequently covering arrays, which represent test sets."""
from pathlib import Path
from typing import Generator
import nltk
from nltk.corpus import wordnet
import spacy
from .ca_generator import CaGenerator

nltk.download('wordnet')

def accept_token(token) -> bool:
    """Return true if token should be replaced with synonyms.

    Only nouns, verbs and adjectives are currently replaced."""
    return token.pos_ in frozenset(['PROPN', 'NOUN', 'VERB', 'ADJ'])

def convert_type(token):
    """Convert spaCy token types to wordnet token types."""
    if token.pos_ in frozenset(['PROPN', 'NOUN']):
        return wordnet.NOUN
    if token.pos_ in frozenset(['VERB']):
        return wordnet.VERB
    return wordnet.ADJ

def generate_synonyms(sentence: str, number_of_synonyms : int = 3) -> list[list[str]]:
    """Generate synonyms for each word in a sentence.

    Tokenize the sentence, then determine each token's type.
    For tokens accepted by accept_token(), use wordnet to find
    synonyms.
    Non-accepted tokens retain their original wording as the sole
    synonym.

    The resulting list has all synonyms for the i-th word in the
    sentence at the i-th position."""
    nlp = spacy.load("en_core_web_sm")
    synonyms = []
    for (i, token) in enumerate(nlp(sentence)):
        synonyms.append([token.text])
        if accept_token(token):
            for syn in wordnet.synsets(
                    token.text, pos=convert_type(token)
            ):
                for l in syn.lemmas():
                    synonyms[i].append(l.name())
        synonyms[i] = list(dict.fromkeys([
            x.lower() for x in synonyms[i]
        ]))[:number_of_synonyms] # remove duplicates
    return synonyms

def generate_ca(synonyms: list[list[str]], strength: int = 2) -> tuple[Path, int]:
    """Generate a CA for the given list of synonyms and a particular strength."""
    return CaGenerator.get_generator().generate(synonyms, strength)

def consume_payload_from_ca(synonyms: list[list[str]],
                            strength: int = 2) -> Generator[str, None, None]:
    """Read lines from a CA and convert it to vectors of synonyms.

    Split each line in the CA by commas, then convert the values
    to int and use them to select the v-th synonym of the k-th word."""

    # Ensure that the first row is unmodified (no synonyms applied)
    yield ' '.join([s[0] for s in synonyms])

    # All other rows are translated
    for line in CaGenerator.get_generator().read(synonyms, strength):
        if all([x=='0' for x in line.strip().split(',')]):
            continue  # Skip all-zero rows (we already forced it above)
        yield ' '.join([
            synonyms[k][int(v)].replace("_", " ")
            for (k,v) in enumerate(line.strip().split(','))
        ])
