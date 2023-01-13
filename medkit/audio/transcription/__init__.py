__all__ = [
    "DocTranscriber",
    "TranscriberFunction",
    "TranscriberFunctionDescription",
    "TranscribedDocument",
]

from medkit.core.utils import modules_are_available

from .doc_transcriber import (
    DocTranscriber,
    TranscriberFunction,
    TranscriberFunctionDescription,
)
from .transcribed_document import TranscribedDocument

if modules_are_available(["torchaudio", "transformers"]):
    # fmt: off
    from .hf_transcriber_function import HFTranscriberFunction  # noqa: F401
    __all__.append("HFTranscriberFunction")
    # fmt: on

if modules_are_available(["torch", "speechbrain"]):
    # fmt: off
    from .sb_transcriber_function import SBTranscriberFunction  # noqa: F401
    __all__.append("SBTranscriberFunction")
    # fmt: on
