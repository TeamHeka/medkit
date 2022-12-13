__all__ = []

import importlib.util

_webrtcvad_is_available = importlib.util.find_spec("webrtcvad") is not None
if _webrtcvad_is_available:
    # fmt: off
    from .webrtc_voice_detector import WebRTCVoiceDetector  # noqa: F401
    __all__.append("WebRTCVoiceDetector")
    # fmt: on

_torch_is_available = importlib.util.find_spec("torch") is not None
_pyannote_audio_is_available = importlib.util.find_spec("pyannote.audio") is not None
if _torch_is_available and _pyannote_audio_is_available:
    # fmt: off
    from .pa_speaker_detector import PASpeakerDetector  # noqa: F401
    __all__.append("PASpeakerDetector")
    # fmt: on
