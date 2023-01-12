__all__ = []

from medkit.core.utils import modules_are_available

# -----------------------------------------------------
# Import optional modules if dependencies are installed
# -----------------------------------------------------

# HF translator module
if modules_are_available(["torch", "transformers"]):
    # fmt: off
    from .hf_translator import HFTranslator  # noqa: F401
    __all__.append("HFTranslator")
    # fmt: on
