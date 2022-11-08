import pytest

pytest.importorskip(modname="torchaudio", reason="torchaudio is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")

import numpy as np  # noqa: E402

from medkit.core.audio import FileAudioBuffer, MemoryAudioBuffer  # noqa: E402
from medkit.audio.transcription.hf_transcriber_function import (  # noqa: E402
    HFTranscriberFunction,
)


_AUDIO = FileAudioBuffer("tests/data/audio/voice.ogg")
_TEXT = "Hello this is my voice i am speaking to you."


@pytest.fixture(scope="module")
def transcriber_func():
    return HFTranscriberFunction()


@pytest.fixture(scope="module")
def transcriber_func_no_dot_no_capitalize():
    return HFTranscriberFunction(add_trailing_dot=False, capitalize=False)


def test_basic(transcriber_func):
    text = transcriber_func.transcribe([_AUDIO])[0]
    assert text == _TEXT


def test_no_dot_no_capitalize(transcriber_func_no_dot_no_capitalize):
    text = transcriber_func_no_dot_no_capitalize.transcribe([_AUDIO])[0]
    assert text == _TEXT.lower()[:-1]


def test_batch(transcriber_func):
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
    # check that result is identical to transcribing one by one
    for audio, text in zip(audios, texts):
        expected_text = transcriber_func.transcribe([audio])[0]
        assert text == expected_text
