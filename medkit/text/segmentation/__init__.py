__all__ = ["SectionTokenizer", "SentenceTokenizer", "SyntagmaTokenizer"]


from medkit.core.utils import modules_are_available

from .section_tokenizer import SectionTokenizer
from .sentence_tokenizer import SentenceTokenizer
from .syntagma_tokenizer import SyntagmaTokenizer

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# Rush sentence tokenizer module
if modules_are_available(["PyRuSH"]):
    # fmt: off
    from .rush_sentence_tokenizer import RushSentenceTokenizer  # noqa: F401
    __all__.append("RushSentenceTokenizer")
    # fmt: on
