__all__ = [
    "get_text_documents",
    "get_text_document",
    "get_text",
    "get_path_hf_dummy_vocab",
]

from pathlib import Path

from medkit.core.text import TextDocument

_PATH_TO_TEXT_DOCS = Path(__file__).parent / "data" / "text"
_PATH_HF_DUMMY_VOCAB = Path(__file__).parent / "data" / "dummy_hf_vocab" / "vocab.txt"


def get_path_hf_dummy_vocab():
    return _PATH_HF_DUMMY_VOCAB


def get_text_documents():
    docs = []
    for path in _PATH_TO_TEXT_DOCS.glob("*.txt"):
        with open(path) as f:
            text = f.read()
        doc = TextDocument(text=text)
        docs.append(doc)
    return docs


def get_text_document(name):
    path = _PATH_TO_TEXT_DOCS / (name + ".txt")
    with open(path) as f:
        text = f.read()
    return TextDocument(text=text)


def get_text(name):
    path = _PATH_TO_TEXT_DOCS / (name + ".txt")
    with open(path) as f:
        text = f.read()
    return text
