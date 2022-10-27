import pytest

pytest.importorskip(modname="torchaudio", reason="torchaudio is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

from medkit.core.audio import FileAudioBuffer, MemoryAudioBuffer  # noqa: E402
from medkit.audio.transcription.hf_transcriber import HFTranscriber  # noqa: E402


_PATH_TO_VOICE_FILE = Path(__file__).parent / ".." / "resources" / "voice.ogg"
_AUDIO = FileAudioBuffer(_PATH_TO_VOICE_FILE)
_TEXT = "Hello this is my voice i am speaking to you."


@pytest.fixture(scope="module")
def transcriber():
    return HFTranscriber()


@pytest.fixture(scope="module")
def transcriber_no_dot_no_capitalize():
    return HFTranscriber(add_trailing_dot=False, capitalize=False)


def test_basic(transcriber):
    text = transcriber.run([_AUDIO])[0]
    assert text == _TEXT


def test_no_dot_no_capitalize(transcriber_no_dot_no_capitalize):
    text = transcriber_no_dot_no_capitalize.run([_AUDIO])[0]
    assert text == _TEXT.lower()[:-1]


def test_batch(transcriber):
    # generate batch of different audios by duplicating signal every other time
    audios = []
    short_signal = _AUDIO.read()
    long_signal = np.concatenate((short_signal, short_signal), axis=1)
    for i in range(10):
        signal = short_signal if i % 2 else long_signal
        audio = MemoryAudioBuffer(signal, _AUDIO.sample_rate)
        audios.append(audio)

    # transcribe batch of audios
    texts = transcriber.run(audios)
    assert len(texts) == len(audios)
    # check that result is identical to transcribing one by one
    for audio, text in zip(audios, texts):
        expected_text = transcriber.run([audio])[0]
        assert text == expected_text
