__all__ = ["TranscribedDocument"]

from typing import Any, Dict, List, Optional

from medkit.core import Store
from medkit.core.audio import Span as AudioSpan
from medkit.core.text import (
    TextDocument,
    Span as TextSpan,
    AnySpanType as AnyTextSpanType,
    span_utils as text_span_utils,
)


class TranscribedDocument(TextDocument):
    """Subclass for :class:`~medkit.core.text.document.TextDocument` instances generated
    by audio transcription."""

    def __init__(
        self,
        text: str,
        text_spans_to_audio_spans: Dict[TextSpan, AudioSpan],
        audio_doc_id: Optional[str],
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        store: Optional[Store] = None,
    ):
        """
        Parameters
        ----------
        text:
            The full transcribed text.
        text_spans_to_audio_spans:
            Mapping between text characters spans in this document and
            corresponding audio spans in the original audio.
        audio_doc_id:
            Id of the original
            :class:`~medkit.core.audio.document.AudioDocument` that was
            transcribed, if known.
        doc_id:
            Document identifier.
        metadata:
            Document metadata.
        store:
            Store to use for annotations.
        """
        assert all(s.end <= len(text) for s in text_spans_to_audio_spans)

        super().__init__(doc_id=doc_id, text=text, metadata=metadata, store=store)

        self.audio_doc_id = audio_doc_id
        self.text_spans_to_audio_spans = text_spans_to_audio_spans

    def get_containing_audio_spans(
        self, text_ann_spans: List[AnyTextSpanType]
    ) -> List[AudioSpan]:
        """Return the audio spans used to transcribe the text referenced by a text
        annotation.

        For instance, if the audio ranging from 1.0 to 20.0 seconds is
        transcribed to some text ranging from character 10 to 56 in the
        transcribed document, and then a text annotation is created referencing
        the span 15 to 25, then the containing audio span will be the one ranging
        from 1.0 to 20.0 seconds.

        Note that some text annotations maybe be contained in more that one
        audio spans.

        Parameters
        ----------
        text_ann_spans:
            Text spans of a text annotation referencing some characters in the
            transcribed document.

        Returns
        -------
        List[AudioSpan]
            Audio spans used to transcribe the text referenced by the spans of `text_ann`.
        """
        ann_text_spans = text_span_utils.normalize_spans(text_ann_spans)
        # TODO: use interval tree instead of nested iteration
        audio_spans = [
            audio_span
            for ann_text_span in ann_text_spans
            for text_span, audio_span in self.text_spans_to_audio_spans.items()
            if text_span.overlaps(ann_text_span)
        ]
        return audio_spans

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        text_spans = [s.to_dict() for s in self.text_spans_to_audio_spans]
        audio_spans = [s.to_dict() for s in self.text_spans_to_audio_spans.values()]
        data.update(
            audio_doc_id=self.audio_doc_id,
            text_spans=text_spans,
            audio_spans=audio_spans,
        )
        return data

    # TODO: add corresponding from_dict() method
