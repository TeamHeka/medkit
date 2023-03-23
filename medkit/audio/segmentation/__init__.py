__all__ = []

from medkit.core.utils import modules_are_available

if modules_are_available(["webrtcvad"]):
    # fmt: off
    from .webrtc_voice_detector import WebRTCVoiceDetector  # noqa: F401
    __all__.append("WebRTCVoiceDetector")
    # fmt: on

if modules_are_available(["torch", "pyannote.audio"]):
    # fmt: off
    from .pa_speaker_detector import PASpeakerDetector  # noqa: F401
    __all__.append("PASpeakerDetector")
    # fmt: on
