import pytest

pytest.importorskip(modname="torchaudio", reason="torchaudio is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")
pytest.importorskip(modname="speechbrain", reason="speechbrain is not installed")

import numpy as np  # noqa: E402

from medkit.core.audio import FileAudioBuffer, MemoryAudioBuffer  # noqa: E402
from medkit.audio.transcription import SBTranscriberFunction  # noqa: E402


_MODEL = "speechbrain/asr-wav2vec2-commonvoice-en"
_AUDIO = FileAudioBuffer("tests/data/audio/voice.ogg")
_EXPECTED_TEXT = "Hello this is my voice i m speaking to you."


def test_basic():
    """Basic behavior"""

    transcriber_func = SBTranscriberFunction(model=_MODEL, needs_decoder=True)
    texts = transcriber_func.transcribe([_AUDIO])
    assert texts == [_EXPECTED_TEXT]


@pytest.mark.parametrize("batch_size", [1, 5, 10, 15])
def test_batch(batch_size):
    """Various batch sizes (smallest, half, exact number of items, more than)"""

    transcriber_func = SBTranscriberFunction(
        model=_MODEL,
        needs_decoder=True,
        batch_size=batch_size,
    )

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
