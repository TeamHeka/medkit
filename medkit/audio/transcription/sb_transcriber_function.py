"""
This module needs extra-dependencies not installed as core dependencies of medkit.
To install them, use `pip install medkit-lib[sb-transcriber_function]`.
"""

__all__ = ["SBTranscriberFunction"]

from pathlib import Path
from typing import List, Optional, Union

import speechbrain as sb

from medkit.core.audio import AudioBuffer
import medkit.core.utils
from medkit.audio.transcription.doc_transcriber import TranscriberFunctionDescription


class SBTranscriberFunction:
    """Transcriber function based on a SpeechBrain model.

    To be used within a
    :class:`~medkit.audio.transcription.doc_transcriber.DocTranscriber`
    """

    def __init__(
        self,
        model: Union[str, Path],
        needs_decoder: bool,
        add_trailing_dot: bool = True,
        capitalize: bool = True,
        cache_dir: Optional[Union[str, Path]] = None,
        device: int = -1,
        batch_size: int = 1,
    ):
        """
        Parameters
        ----------
        model:
            Name of the model on the Hugging Face models hub, or local path.
        needs_decoder:
            Whether the model should be used with the speechbrain
            `EncoderDecoderASR` class or the `EncoderASR` class. If unsure,
            check the code snippets on the model card on the hub.
        add_trailing_dot:
            If `True`, a dot will be added at the end of each transcription text.
        capitalize:
            It `True`, the first letter of each transcription text will be
            uppercased and the rest lowercased.
        cache_dir:
            Directory where to store the downloaded model. If `None`,
            speechbrain will use "pretrained_models/" and "model_checkpoints/"
            directories in the current working directory.
        device:
            Device to use for pytorch models. Follows the Hugging Face convention
            (`-1` for cpu and device number for gpu, for instance `0` for "cuda:0")
        batch_size:
            Number of segments in batches processed by the model.
        """
        if cache_dir is not None:
            cache_dir = Path(cache_dir)

        self.model_name = model
        self.add_trailing_dot = add_trailing_dot
        self.capitalize = capitalize
        self.cache_dir = cache_dir
        self.device = device
        self.batch_size = batch_size
        self._torch_device = "cpu" if self.device < 0 else f"cuda:{self.device}"

        asr_class = (
            sb.pretrained.EncoderDecoderASR
            if needs_decoder
            else sb.pretrained.EncoderASR
        )

        self._asr = asr_class.from_hparams(
            source=model, savedir=cache_dir, run_opts={"device": self._torch_device}
        )

        self._sample_rate = self._asr.audio_normalizer.sample_rate

    @property
    def description(self) -> TranscriberFunctionDescription:
        config = dict(
            model_name=self.model_name,
            has_decoder=self.has_decoder,
            add_trailing_dot=self.add_trailing_dot,
            capitalize=self.capitalize,
            cache_dir=self.cache_dir,
            device=self.device,
            batch_size=self.batch_size,
        )
        return TranscriberFunctionDescription(
            name=self.__class__.__name__, config=config
        )

    def transcribe(self, audios: List[AudioBuffer]) -> List[str]:
        if not all(a.sample_rate == self._sample_rate for a in audios):
            raise ValueError(
                "SBTranscriberFunction received audio buffers with incompatible sample"
                f" rates (model expected {self._sample_rate} Hz)"
            )
        if not all(a.nb_channels == 1 for a in audios):
            raise ValueError("SBTranscriberFunction only supports mono audio buffers")

        texts = []
        for batched_audios in medkit.core.utils.batch_list(audios, self.batch_size):
            texts += self._transcribe_audios(batched_audios)
        return texts

    def _transcribe_audios(self, audios: List[AudioBuffer]) -> List[str]:
        # group audios in batch of same length with padding
        padded_batch = sb.dataio.batch.PaddedBatch(
            [{"wav": a.read().reshape((-1,))} for a in audios]
        )
        padded_batch.to(self._torch_device)

        texts, _ = self._asr.transcribe_batch(
            padded_batch.wav.data, padded_batch.wav.lengths
        )

        if self.capitalize:
            texts = [t.capitalize() for t in texts]
        if self.add_trailing_dot:
            texts = [t + "." for t in texts]

        return texts
