__all__ = []

from medkit.core.utils import has_optional_modules

if has_optional_modules(["webrtcvad"]):
    # fmt: off
    from .webrtc_voice_detector import WebRTCVoiceDetector  # noqa: F401
    __all__.append("WebRTCVoiceDetector")
    # fmt: on

if has_optional_modules(["torch", "pyannote.audio"]):
    # fmt: off
    from .pa_speaker_detector import PASpeakerDetector  # noqa: F401
    __all__.append("PASpeakerDetector")
    # fmt: on
