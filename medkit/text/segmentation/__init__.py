__all__ = ["SectionTokenizer", "SentenceTokenizer", "SyntagmaTokenizer"]


from medkit.core.utils import has_optional_modules

from .section_tokenizer import SectionTokenizer
from .sentence_tokenizer import SentenceTokenizer
from .syntagma_tokenizer import SyntagmaTokenizer

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# Rush sentence tokenizer module
if has_optional_modules(["PyRuSH"]):
    # fmt: off
    from .rush_sentence_tokenizer import RushSentenceTokenizer  # noqa: F401
    __all__.append("RushSentenceTokenizer")
    # fmt: on
