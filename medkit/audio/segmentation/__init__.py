__all__ = []

import importlib.util

_webrtcvad_is_available = importlib.util.find_spec("webrtcvad") is not None
if _webrtcvad_is_available:
    # fmt: off
    from .webrtc_voice_detector import WebRTCVoiceDetector  # noqa: F401
    __all__.append("WebRTCVoiceDetector")
    # fmt: on
