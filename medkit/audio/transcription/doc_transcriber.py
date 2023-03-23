from __future__ import annotations

__all__ = ["DocTranscriber", "TranscriberFunction", "TranscriberFunctionDescription"]

import dataclasses
from typing import Any, Dict, List, Optional
from typing_extensions import Protocol

from medkit.audio.transcription.transcribed_document import TranscribedDocument
from medkit.core import Operation
from medkit.core.audio import AudioDocument, AudioBuffer, Segment as AudioSegment
from medkit.core.text import Segment as TextSegment, Span as TextSpan


class TranscriberFunction(Protocol):
    """Protocol for components in charge of the actual speech-to-text transcription
    to use with :class:`~.DocTranscriber`"""

    """Description of the transcriber"""
    description: TranscriberFunctionDescription

    def transcribe(self, audios: List[AudioBuffer]) -> List[str]:
        """Convert audio buffers into strings by performing speech-to-text.

        Parameters
        ----------
        audios:
            Audio buffers to converted

        Returns
        -------
        List[str]
            Text transcription for each buffer in `audios`
        """
        pass


@dataclasses.dataclass
class TranscriberFunctionDescription:
    """Description of a specific instance of a transcriber function (similarly to
    :class:`~medkit.core.operation_desc.OperationDescription`).

    Parameters
    ----------
    name:
        The name of the transcriber function (typically the class name).
    config:
        The specific configuration of the instance.
    """

    name: str
    config: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(name=self.name, config=self.config)


class DocTranscriber(Operation):
    """Speech-to-text transcriber generating text documents from audio documents.

    For each text document, all audio segments with a specific label are
    converted into text segments and regrouped in a corresponding new text
    document. The text of each segment is concatenated to form the full raw text
    of the new document.

    Generated text documents are instances of
    :class:`~medkit.audio.transcription.transcribed_document.TranscribedDocument`
    (subclass of :class:`~medkit.core.text.document.TextDocument`) with
    additional info such as the identifier of the original audio document and a mapping
    between audio spans and text spans.

    Methods :func: `create_text_segment()` and :func:
    `augment_full_text_for_next_segment()` can be overridden to customize how
    the text segments are created and how they are concatenated to form the full
    text.

    The actual transcription task is delegated to a :class:`~.TranscriberFunction`
    that must be provided.
    """

    def __init__(
        self,
        input_label: str,
        output_label: str,
        transcriber_func: TranscriberFunction,
        attrs_to_copy: Optional[List[str]] = None,
        uid: Optional[str] = None,
    ):
        """
        Parameters
        ----------
        input_label:
            Label of audio segments that should be transcribed.
        output_label:
            Label of generated text segments.
        transcriber_func:
            Transcription component in charge of actually transforming each
            audio signal into text.
        attrs_to_copy:
            Labels of attributes that should be copied from the original audio segments
            to the transcribed text segments.
        uid:
            Identifier of the transcriber.
        """

        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        if attrs_to_copy is None:
            attrs_to_copy = []

        self.input_label = input_label
        self.output_label = output_label
        self.transcriber_func = transcriber_func
        self.attrs_to_copy = attrs_to_copy

    def run(self, audio_docs: List[AudioDocument]) -> List[TranscribedDocument]:
        """Return a transcribed text document for each document in `audio_docs`

        Parameters
        ----------
        audio_docs:
            Audio documents to transcribe

        Returns
        -------
        List[TranscribedDocument]:
            Transcribed text documents (once per document in `audio_docs`)
        """
        return [self._transcribe_doc(d) for d in audio_docs]

    def _transcribe_doc(self, audio_doc: AudioDocument) -> TranscribedDocument:
        # get all audio segments with specified label
        audio_segs = audio_doc.anns.get(label=self.input_label)
        # transcribe them to text
        audios = [seg.audio for seg in audio_segs]
        texts = self.transcriber_func.transcribe(audios)

        # rebuild full text and segments from transcribed texts
        full_text = ""
        text_segs = []
        text_spans_to_audio_spans = {}

        for text, audio_seg in zip(texts, audio_segs):
            # handle joining between segments
            full_text = self.augment_full_text_for_next_segment(
                full_text, text, audio_seg
            )
            # compute text span
            start = len(full_text)
            full_text += text
            end = len(full_text)
            span = TextSpan(start, end)
            # create TextSegment with proper span referencing full text
            text_seg = TextSegment(label=self.output_label, spans=[span], text=text)

            # copy attrs from audio segment
            for label in self.attrs_to_copy:
                for attr in audio_seg.attrs.get(label=label):
                    copied_attr = attr.copy()
                    text_seg.attrs.add(copied_attr)
                    # handle provenance
                    if self._prov_tracer is not None:
                        self._prov_tracer.add_prov(
                            copied_attr, self.description, [attr]
                        )

            text_segs.append(text_seg)

            # store mapping between text and audio span
            text_spans_to_audio_spans[span] = audio_seg.span

            # handle provenance (text segment generated from audio segment)
            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(text_seg, self.description, [audio_seg])

        text_doc = TranscribedDocument(
            text=full_text,
            audio_doc_id=audio_doc.uid,
            text_spans_to_audio_spans=text_spans_to_audio_spans,
        )
        for text_seg in text_segs:
            text_doc.anns.add(text_seg)
        # TODO should this be handled by provenance?
        # if self._prov_tracer is not None:
        #     self._prov_tracer.add_prov(
        #         text_doc, self, source_data_items=[audio_doc]
        #     )
        return text_doc

    def augment_full_text_for_next_segment(
        self, full_text: str, segment_text: str, audio_segment: AudioSegment
    ) -> str:
        """Append intermediate joining text to full text before the next segment is
        concatenated to it. Override for custom behavior."""
        if len(full_text) > 0:
            full_text += "\n"
        return full_text
