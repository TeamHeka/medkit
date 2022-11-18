import pytest

pytest.importorskip(modname="torchaudio", reason="torchaudio is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")
pytest.importorskip(modname="speechbrain", reason="speechbrain is not installed")

import numpy as np  # noqa: E402
import torch  # noqa: E402

from medkit.core.audio import MemoryAudioBuffer  # noqa: E402
from medkit.audio.transcription import SBTranscriberFunction  # noqa: E402

_MOCK_MODEL_NAME = "mock-model"
_SAMPLE_RATE = 16000
_TEXT_TEMPLATE = "AUDIO HAS {} SAMPLES"


# mock of speechbrain.pretrained.EncoderASR and
# speechbrain.pretrained.EncoderDecoderASR classes used by SBTranscriberFunction
class _MockSpeechbrainASR:
    def __init__(self):
        # original class stores AudioNormalizer instance that we use to check
        # the sample rate
        self.audio_normalizer = _MockAudioNormalizer()

    @classmethod
    def from_hparams(cls, source, savedir, run_opts):
        assert source == _MOCK_MODEL_NAME
        return cls()

    def transcribe_batch(self, wavs, wav_lengths):
        assert isinstance(wavs, torch.Tensor) and wavs.ndim == 2
        assert isinstance(wav_lengths, torch.Tensor) and wav_lengths.ndim == 1

        # for each wav in batch, return string containing sample count (allows
        # us to check that each audio input has corresponding output)
        texts = []
        for wav_length in wav_lengths:
            # convert speechbrain relative length to absolute sample count
            nb_samples = int(wavs.shape[-1] * wav_length)
            text = _TEXT_TEMPLATE.format(nb_samples)
            texts.append(text)

        # original class returns tuple of texts and tokens but we only use
        # texts
        return texts, None


class _MockAudioNormalizer:
    def __init__(self):
        self.sample_rate = _SAMPLE_RATE


@pytest.fixture(scope="module", autouse=True)
def _mocked_asr(module_mocker):
    module_mocker.patch("speechbrain.pretrained.EncoderASR", _MockSpeechbrainASR)
    module_mocker.patch("speechbrain.pretrained.EncoderDecoderASR", _MockSpeechbrainASR)


def _gen_audio(nb_samples):
    return MemoryAudioBuffer(signal=np.zeros((1, nb_samples)), sample_rate=_SAMPLE_RATE)


def test_basic():
    """Basic behavior"""

    transcriber_func = SBTranscriberFunction(
        model=_MOCK_MODEL_NAME, needs_decoder=False
    )
    texts = transcriber_func.transcribe([_gen_audio(1000), _gen_audio(2000)])
    assert texts == ["Audio has 1000 samples.", "Audio has 2000 samples."]


def test_no_formatting():
    """No reformatting of transcribed text (raw text as returned by speechbrain ASR)"""

    transcriber_func = SBTranscriberFunction(
        model=_MOCK_MODEL_NAME,
        needs_decoder=False,
        add_trailing_dot=False,
        capitalize=False,
    )
    texts = transcriber_func.transcribe([_gen_audio(1000)])
    assert texts == ["AUDIO HAS 1000 SAMPLES"]
