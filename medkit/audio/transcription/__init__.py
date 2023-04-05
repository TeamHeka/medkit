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
    __all__.append("hf_transcriber_function")

if modules_are_available(["torch", "speechbrain"]):
    __all__.append("sb_transcriber_function")
