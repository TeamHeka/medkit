__all__ = []

from medkit.core.utils import has_optional_modules

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# HF translator module
if has_optional_modules(["torch", "transformers"]):
    # fmt: off
    from .hf_translator import HFTranslator  # noqa: F401
    __all__.append("HFTranslator")
    # fmt: on
