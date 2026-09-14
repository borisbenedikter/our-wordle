"""
Build definitions.json from possible_answers.txt.

Primary source:
    NLTK WordNet

Fallback source:
    Datamuse API (definitions metadata)
    Used ONLY when WordNet has no definition for a word.

Usage:
    python build_definitions.py

Expected files:
    build_definitions.py
    possible_answers.txt

Output:
    definitions.json

Install dependency if needed:
    pip install nltk

Notes:
- WordNet data is downloaded automatically if it is not installed.
- Internet access is needed only for words that WordNet cannot define.
- At most MAX_DEFINITIONS_PER_POS definitions are stored for each
  part of speech (noun, verb, adjective, adverb, etc.).
"""

import json
import time
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import nltk
from nltk.corpus import wordnet as wn


INPUT_FILE = Path("possible_answers.txt")
OUTPUT_FILE = Path("definitions.json")

WORD_LENGTH = 5

# Maximum number of distinct senses stored PER part of speech.
MAX_DEFINITIONS_PER_POS = 2

# Fallback API behavior.
API_TIMEOUT_SECONDS = 5
API_RETRIES = 1
API_DELAY_SECONDS = 0.10

DATAMUSE_API_URL = "https://api.datamuse.com/words"

POS_NAMES = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "adjective",
    "r": "adverb",
}

DATAMUSE_POS_NAMES = {
    "n": "noun",
    "v": "verb",
    "adj": "adjective",
    "adv": "adverb",
    "u": "unknown",
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


def can_add_definition(counts_by_pos, part_of_speech):
    """Return True if this part of speech has not reached its limit."""
    return counts_by_pos[part_of_speech] < MAX_DEFINITIONS_PER_POS


def get_wordnet_definitions(word):
    """
    Return distinct WordNet senses, with at most
    MAX_DEFINITIONS_PER_POS senses for each part of speech.
    """
    entries = []
    seen_definitions = set()
    counts_by_pos = defaultdict(int)

    for synset in wn.synsets(word):
        definition = synset.definition().strip()

        if not definition:
            continue

        normalized = definition.lower()

        if normalized in seen_definitions:
            continue

        part_of_speech = POS_NAMES.get(
            synset.pos(),
            synset.pos(),
        )

        if not can_add_definition(
            counts_by_pos,
            part_of_speech,
        ):
            continue

        seen_definitions.add(normalized)

        entry = {
            "partOfSpeech": part_of_speech,
            "definition": definition,
            "source": "wordnet",
        }

        examples = synset.examples()

        if examples:
            entry["example"] = examples[0]

        entries.append(entry)
        counts_by_pos[part_of_speech] += 1

    return entries


def parse_datamuse_definition(raw_definition):
    """
    Datamuse definitions are commonly returned in the form:

        "n\\tdefinition text"
        "v\\tdefinition text"
        "adj\\tdefinition text"

    Return (part_of_speech, definition).
    """
    if "\t" in raw_definition:
        pos_code, definition = raw_definition.split("\t", 1)
        part_of_speech = DATAMUSE_POS_NAMES.get(
            pos_code.strip(),
            pos_code.strip(),
        )
    else:
        part_of_speech = "unknown"
        definition = raw_definition

    return part_of_speech, definition.strip()


def get_datamuse_definitions(word):
    """
    Query Datamuse for dictionary definitions.

    Returns distinct senses, with at most MAX_DEFINITIONS_PER_POS
    senses for each part of speech.
    Returns [] if no usable definition is found.
    """
    params = urlencode({
        "sp": word,
        "md": "d",
        "max": 10,
    })

    url = f"{DATAMUSE_API_URL}?{params}"

    request = Request(
        url,
        headers={
            "User-Agent": "word-game-definition-builder/1.0"
        },
    )

    data = None

    for attempt in range(API_RETRIES + 1):
        try:
            with urlopen(
                request,
                timeout=API_TIMEOUT_SECONDS
            ) as response:
                data = json.loads(response.read().decode("utf-8"))
            break

        except HTTPError as error:
            print(
                f"\n  Datamuse HTTP error for '{word}': "
                f"{error.code}"
            )

        except URLError as error:
            print(
                f"\n  Datamuse connection error for '{word}': "
                f"{error.reason}"
            )

        except TimeoutError:
            print(
                f"\n  Datamuse timeout for '{word}' "
                f"(attempt {attempt + 1}/{API_RETRIES + 1})"
            )

        except json.JSONDecodeError as error:
            print(
                f"\n  Datamuse JSON error for '{word}': {error}"
            )
            return []

        if attempt < API_RETRIES:
            time.sleep(0.5)

    if not isinstance(data, list) or not data:
        return []

    exact_matches = [
        item
        for item in data
        if item.get("word", "").lower() == word.lower()
    ]

    candidates = exact_matches if exact_matches else data

    entries = []
    seen_definitions = set()
    counts_by_pos = defaultdict(int)

    for item in candidates:
        for raw_definition in item.get("defs", []):
            part_of_speech, definition = (
                parse_datamuse_definition(raw_definition)
            )

            if not definition:
                continue

            normalized = definition.lower()

            if normalized in seen_definitions:
                continue

            if not can_add_definition(
                counts_by_pos,
                part_of_speech,
            ):
                continue

            seen_definitions.add(normalized)

            entries.append({
                "partOfSpeech": part_of_speech,
                "definition": definition,
                "source": "datamuse",
            })

            counts_by_pos[part_of_speech] += 1

    return entries


def main():
    ensure_wordnet()

    words = load_words(INPUT_FILE)

    print(f"Loaded {len(words)} possible answers.")
    print("Checking WordNet first...")

    definitions = {}
    wordnet_missing = []

    # ---------------------------------------------------------
    # PASS 1: WordNet
    # ---------------------------------------------------------
    for word in words:
        entries = get_wordnet_definitions(word)

        if entries:
            definitions[word] = entries
        else:
            wordnet_missing.append(word)

    print()
    print(
        f"WordNet found definitions for "
        f"{len(words) - len(wordnet_missing)} word(s)."
    )
    print(
        f"WordNet missed {len(wordnet_missing)} word(s)."
    )

    # ---------------------------------------------------------
    # PASS 2: Datamuse, only for WordNet misses
    # ---------------------------------------------------------
    still_missing = []

    if wordnet_missing:
        print()
        print("Trying Datamuse for WordNet misses...")

        for index, word in enumerate(wordnet_missing, start=1):
            print(
                f"[{index}/{len(wordnet_missing)}] {word}",
                end="",
                flush=True,
            )

            entries = get_datamuse_definitions(word)

            if entries:
                definitions[word] = entries
                print("  -> found")
            else:
                definitions[word] = []
                still_missing.append(word)
                print("  -> not found")

            time.sleep(API_DELAY_SECONDS)

    definitions = dict(sorted(definitions.items()))

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            definitions,
            file,
            ensure_ascii=False,
            indent=2,
        )

    wordnet_count = sum(
        1
        for entries in definitions.values()
        if entries and entries[0].get("source") == "wordnet"
    )

    datamuse_count = sum(
        1
        for entries in definitions.values()
        if entries and entries[0].get("source") == "datamuse"
    )

    print()
    print("=" * 50)
    print(f"Created '{OUTPUT_FILE}' with {len(definitions)} words.")
    print(f"Maximum definitions per part of speech: {MAX_DEFINITIONS_PER_POS}")
    print(f"Defined by WordNet:        {wordnet_count}")
    print(f"Defined by Datamuse:       {datamuse_count}")
    print(f"Still without definition:  {len(still_missing)}")

    if still_missing:
        print()
        print("Words still missing:")
        print(", ".join(still_missing))
    else:
        print()
        print("Every possible answer now has at least one definition.")


if __name__ == "__main__":
    main()
