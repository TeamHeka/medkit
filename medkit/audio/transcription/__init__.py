__all__ = [
    "DocTranscriber",
    "TranscriberFunction",
    "TranscriberFunctionDescription",
    "TranscribedDocument",
]

from medkit.core.utils import has_optional_modules

from .doc_transcriber import (
    DocTranscriber,
    TranscriberFunction,
    TranscriberFunctionDescription,
)
from .transcribed_document import TranscribedDocument

if has_optional_modules(["torchaudio", "transformers"]):
    # fmt: off
    from .hf_transcriber_function import HFTranscriberFunction  # noqa: F401
    __all__.append("HFTranscriberFunction")
    # fmt: on

if has_optional_modules(["torch", "speechbrain"]):
    # fmt: off
    from .sb_transcriber_function import SBTranscriberFunction  # noqa: F401
    __all__.append("SBTranscriberFunction")
    # fmt: on
