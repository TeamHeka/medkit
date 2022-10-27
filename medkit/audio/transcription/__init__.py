__all__ = [
    "DocTranscriber",
    "AudioTranscriber",
    "AudioTranscriberDescription",
    "TranscribedDocument",
]

import importlib.util

from .doc_transcriber import (
    DocTranscriber,
    AudioTranscriber,
    AudioTranscriberDescription,
)
from .transcribed_document import TranscribedDocument

_torchaudio_is_available = importlib.util.find_spec("torchaudio") is not None
_transformers_is_available = importlib.util.find_spec("transformers") is not None
if _torchaudio_is_available and _transformers_is_available:
    # fmt: off
    from .hf_transcriber import HFTranscriber  # noqa: F401
    __all__.append("HFTranscriber")
    # fmt: on

_torch_is_available = importlib.util.find_spec("torch") is not None
_speechbrain_is_available = importlib.util.find_spec("speechbrain") is not None
if _speechbrain_is_available and _torch_is_available and _transformers_is_available:
    # fmt: off
    from .sb_transcriber import SBTranscriber  # noqa: F401
    __all__.append("SBTranscriber")
    # fmt: on
