"""
Build definitions.json from possible_answers.txt using NLTK WordNet.

Usage:
    python build_definitions.py

Expected files:
    build_definitions.py
    possible_answers.txt

Output:
    definitions.json

Install dependency if needed:
    pip install nltk
"""

import json
from pathlib import Path

import nltk
from nltk.corpus import wordnet as wn


INPUT_FILE = Path("possible_answers.txt")
OUTPUT_FILE = Path("definitions.json")

# Maximum number of distinct dictionary senses stored for each word.
MAX_DEFINITIONS_PER_WORD = 3

WORD_LENGTH = 5

POS_NAMES = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "adjective",
    "r": "adverb",
}


def ensure_wordnet():
    """Download WordNet data if it is not already installed."""
    try:
        wn.synsets("word")
    except LookupError:
        print("WordNet data not found. Downloading it...")
        nltk.download("wordnet", quiet=False)


def load_words(filename):
    """Load unique five-letter alphabetic words from a text file."""
    if not filename.exists():
        raise FileNotFoundError(
            f"Could not find '{filename}'. "
            "Place this script in the same folder as possible_answers.txt."
        )

    words = set()

    with filename.open("r", encoding="utf-8") as file:
        for line in file:
            word = line.strip().lower()

            if len(word) == WORD_LENGTH and word.isalpha():
                words.add(word)

    return sorted(words)


def get_definitions(word):
    """
    Return up to MAX_DEFINITIONS_PER_WORD distinct WordNet senses.

    Each entry has:
        partOfSpeech
        definition
        example      (only when WordNet provides one)
    """
    entries = []
    seen_definitions = set()

    for synset in wn.synsets(word):
        definition = synset.definition().strip()

        normalized = definition.lower()
        if normalized in seen_definitions:
            continue

        seen_definitions.add(normalized)

        entry = {
            "partOfSpeech": POS_NAMES.get(synset.pos(), synset.pos()),
            "definition": definition,
        }

        examples = synset.examples()
        if examples:
            entry["example"] = examples[0]

        entries.append(entry)

        if len(entries) >= MAX_DEFINITIONS_PER_WORD:
            break

    return entries


def main():
    ensure_wordnet()

    words = load_words(INPUT_FILE)

    print(f"Loaded {len(words)} possible answers.")
    print("Building definitions...")

    definitions = {}
    missing_words = []

    for word in words:
        entries = get_definitions(word)
        definitions[word] = entries

        if not entries:
            missing_words.append(word)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            definitions,
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    print()
    print(f"Created '{OUTPUT_FILE}' with {len(definitions)} words.")

    if missing_words:
        print(f"WordNet had no definition for {len(missing_words)} word(s):")
        print(", ".join(missing_words))
    else:
        print("WordNet returned at least one definition for every word.")


if __name__ == "__main__":
    main()
