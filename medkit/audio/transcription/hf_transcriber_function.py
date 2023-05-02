"""
This module needs extra-dependencies not installed as core dependencies of medkit.
To install them, use `pip install medkit-lib[hf-transcriber_function]`.
"""

__all__ = ["HFTranscriberFunction"]

from pathlib import Path
from typing import List, Optional, Union

import transformers
from transformers import AutomaticSpeechRecognitionPipeline

from medkit.core.audio import AudioBuffer
from medkit.audio.transcription.doc_transcriber import TranscriberFunctionDescription


class HFTranscriberFunction:
    """Transcriber function based on a Hugging Face transformers model.

    To be used within a
    :class:`~medkit.audio.transcription.doc_transcriber.DocTranscriber`
    """

    def __init__(
        self,
        model: str = "facebook/s2t-large-librispeech-asr",
        add_trailing_dot: bool = True,
        capitalize: bool = True,
        device: int = -1,
        batch_size: int = 1,
        cache_dir: Optional[Union[str, Path]] = None,
    ):
        """
        Parameters
        ----------
        model:
            Name of the ASR model on the Hugging Face models hub. Must be a
            model compatible with the `AutomaticSpeechRecognitionPipeline`
            transformers class.
        add_trailing_dot:
            If `True`, a dot will be added at the end of each transcription text.
        capitalize:
            It `True`, the first letter of each transcription text will be
            uppercased and the rest lowercased.
        device:
            Device to use for pytorch models. Follows the Hugging Face convention
            (`-1` for cpu and device number for gpu, for instance `0` for "cuda:0")
        batch_size:
            Size of batches processed by ASR pipeline.
        cache_dir:
            Directory where to store downloaded models. If not set, the default
            HuggingFace cache dir is used.
        """
        self.model_name = model
        self.add_trailing_dot = add_trailing_dot
        self.capitalize = capitalize
        self.device = device

        task = transformers.pipelines.get_task(self.model_name)
        if not task == "automatic-speech-recognition":
            raise ValueError(
                f"Model {self.model_name} is not associated to a speech"
                " recognition task and cannot be use with HFTranscriberFunction"
            )

        self._pipeline = transformers.pipeline(
            task=task,
            model=self.model_name,
            feature_extractor=self.model_name,
            pipeline_class=AutomaticSpeechRecognitionPipeline,
            device=self.device,
            batch_size=batch_size,
            model_kwargs={"cache_dir": cache_dir},
        )

    @property
    def description(self) -> TranscriberFunctionDescription:
        config = dict(
            model_name=self.model_name,
            add_trailing_dot=self.add_trailing_dot,
            capitalize=self.capitalize,
            device=self.device,
        )
        return TranscriberFunctionDescription(
            name=self.__class__.__name__, config=config
        )

    def transcribe(self, audios: List[AudioBuffer]) -> List[str]:
        audio_dicts_gen = (
            {
                "raw": audio.read().reshape((-1,)),
                "sampling_rate": audio.sample_rate,
            }
            for audio in audios
        )
        text_dicts = self._pipeline(audio_dicts_gen)
        texts_gen = (text_dict["text"] for text_dict in text_dicts)

        if self.capitalize and self.add_trailing_dot:
            texts = [t.capitalize() + "." for t in texts_gen]
        elif self.capitalize:
            texts = [t.capitalize() for t in texts_gen]
        elif self.add_trailing_dot:
            texts = [t + "." for t in texts_gen]
        else:
            texts = list(texts_gen)

        return texts
