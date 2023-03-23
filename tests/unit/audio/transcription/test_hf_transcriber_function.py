import pytest

pytest.importorskip(modname="torchaudio", reason="torchaudio is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")

import numpy as np  # noqa: E402

from medkit.core.audio import MemoryAudioBuffer  # noqa: E402
from medkit.audio.transcription import HFTranscriberFunction  # noqa: E402


_SAMPLE_RATE = 16000
_TEXT_TEMPLATE = "AUDIO HAS {} SAMPLES"


# mock of AutomaticSpeechRecognitionPipeline class used by HFTranscriberFunction
class _MockPipeline:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, audio_dicts):
        # for each audio dict in batch, return string containing sample count
        # (allows us to check that each audio input has corresponding output)
        text_dicts = []
        for audio_dict in audio_dicts:
            nb_samples = int(audio_dict["raw"].shape[-1])
            text = _TEXT_TEMPLATE.format(nb_samples)
            text_dicts.append({"text": text})

        return text_dicts


@pytest.fixture(scope="module", autouse=True)
def _mocked_pipeline(module_mocker):
    module_mocker.patch(
        "transformers.pipelines.get_task", lambda m: "automatic-speech-recognition"
    )
    module_mocker.patch("transformers.pipeline", _MockPipeline)


def _gen_audio(nb_samples):
    return MemoryAudioBuffer(signal=np.zeros((1, nb_samples)), sample_rate=_SAMPLE_RATE)


def test_basic():
    """Basic behavior"""

    transcriber_func = HFTranscriberFunction(model="mock-model")
    texts = transcriber_func.transcribe([_gen_audio(1000), _gen_audio(2000)])
    assert texts == ["Audio has 1000 samples.", "Audio has 2000 samples."]


def test_no_formatting():
    """No reformatting of transcribed text (raw text as returned by transformers pipeline)
    """

    transcriber_func = HFTranscriberFunction(
        model="mock-model",
        add_trailing_dot=False,
        capitalize=False,
    )
    texts = transcriber_func.transcribe([_gen_audio(1000)])
    assert texts == ["AUDIO HAS 1000 SAMPLES"]
