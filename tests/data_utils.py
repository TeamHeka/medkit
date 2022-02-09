from pathlib import Path

from medkit.core import Collection
from medkit.core.text import TextDocument

_PATH_TO_TEXT_DOCS = Path(__file__).parent / "data" / "text"


def get_text_collection():
    docs = []
    for path in _PATH_TO_TEXT_DOCS.glob("*.txt"):
        with open(path) as f:
            text = f.read()
        doc = TextDocument(text)
        docs.append(doc)
    return Collection(docs)


def get_text_document(name):
    path = _PATH_TO_TEXT_DOCS / (name + ".txt")
    with open(path) as f:
        text = f.read()
    return TextDocument(text)
