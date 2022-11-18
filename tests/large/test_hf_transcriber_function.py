import pytest

pytest.importorskip(modname="torchaudio", reason="torchaudio is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")

import numpy as np  # noqa: E402

from medkit.core.audio import FileAudioBuffer, MemoryAudioBuffer  # noqa: E402
from medkit.audio.transcription import HFTranscriberFunction  # noqa: E402


_MODEL = "facebook/s2t-large-librispeech-asr"
_AUDIO = FileAudioBuffer("tests/data/audio/voice.ogg")
_EXPECTED_TEXT = "Hello this is my voice i am speaking to you."


def test_basic():
    """Basic behavior"""

    transcriber_func = HFTranscriberFunction(model=_MODEL)
    texts = transcriber_func.transcribe([_AUDIO])
    assert texts == [_EXPECTED_TEXT]


def test_batch():
    "Pass batch inputs"

    transcriber_func = HFTranscriberFunction(model=_MODEL)

    # generate batch of different audios by duplicating signal every other time
    audios = []
    short_signal = _AUDIO.read()
    long_signal = np.concatenate((short_signal, short_signal), axis=1)
    for i in range(10):
        signal = short_signal if i % 2 else long_signal
        audio = MemoryAudioBuffer(signal, _AUDIO.sample_rate)
        audios.append(audio)

    # transcribe batch of audios
    texts = transcriber_func.transcribe(audios)
    assert len(texts) == len(audios)

    for audio, text in zip(audios, texts):
        expected_text = transcriber_func.transcribe([audio])[0]
        assert text == expected_text
