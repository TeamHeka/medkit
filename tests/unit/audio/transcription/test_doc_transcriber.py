from medkit.audio.transcription.doc_transcriber import (
    DocTranscriber,
    TranscriberFunction,
    TranscriberFunctionDescription,
)
from medkit.core import Attribute, ProvTracer, DictStore
from medkit.core.audio import (
    AudioDocument,
    Segment as AudioSegment,
    Span as AudioSpan,
    MemoryAudioBuffer,
)
from medkit.core.text import Span as TextSpan
from tests.audio_utils import generate_silence

_SAMPLE_RATE = 4000
_AUDIO_LABEL = "speech"
_TEXT_LABEL = "section"


class _MockTranscriberFunction(TranscriberFunction):
    def __init__(self) -> None:
        self.count = 0

    def transcribe(self, audios):
        texts = []
        for _ in audios:
            self.count += 1
            text = f"This is transcribed text number {self.count}."
            texts.append(text)
        return texts

    def description(self):
        return TranscriberFunctionDescription("TranscriberFunc")


def _get_audio_segment(audio_span):
    signal = generate_silence(audio_span.length, _SAMPLE_RATE)
    audio = MemoryAudioBuffer(signal, _SAMPLE_RATE)
    return AudioSegment(label=_AUDIO_LABEL, span=audio_span, audio=audio)


def _get_audio_doc(audio_spans):
    audio_doc = AudioDocument()
    for audio_span in audio_spans:
        audio_seg = _get_audio_segment(audio_span)
        audio_doc.add_annotation(audio_seg)
    return audio_doc


def test_basic():
    """Basic behavior"""

    # build 2 audio docs with 2 and 1 spans
    audio_span_1 = AudioSpan(0.0, 0.5)
    audio_span_2 = AudioSpan(1.0, 2.5)
    audio_doc_1 = _get_audio_doc([audio_span_1, audio_span_2])
    audio_span_3 = AudioSpan(0.5, 2.0)
    audio_doc_2 = _get_audio_doc([audio_span_3])
    audio_docs = [audio_doc_1, audio_doc_2]

    doc_transcriber = DocTranscriber(
        input_label=_AUDIO_LABEL,
        output_label=_TEXT_LABEL,
        transcriber_func=_MockTranscriberFunction(),
    )
    text_docs = doc_transcriber.run(audio_docs)
    assert len(text_docs) == len(audio_docs)

    # 1st text doc
    text_doc_1 = text_docs[0]
    # reconstructed full text is as expected
    expected_text = (
        "This is transcribed text number 1.\nThis is transcribed text number 2."
    )
    assert text_doc_1.text == expected_text
    # reference to original audio doc
    assert text_doc_1.audio_doc_id == audio_doc_1.id
    # mapping to audio spans in original doc
    text_span_1 = TextSpan(0, 34)
    text_span_2 = TextSpan(35, 69)
    assert text_doc_1.text_spans_to_audio_spans == {
        text_span_1: audio_span_1,
        text_span_2: audio_span_2,
    }

    # has all expected segments
    text_segs_1 = text_doc_1.get_annotations_by_label(_TEXT_LABEL)
    assert len(text_segs_1) == len(audio_doc_1.get_annotations_by_label(_AUDIO_LABEL))

    # segments have corresponding texts and spans
    text_seg_1 = text_segs_1[0]
    assert text_seg_1.label == _TEXT_LABEL
    assert text_seg_1.text == "This is transcribed text number 1."
    assert text_seg_1.spans == [text_span_1]

    text_seg_2 = text_segs_1[1]
    assert text_seg_2.label == _TEXT_LABEL
    assert text_seg_2.text == "This is transcribed text number 2."
    assert text_seg_2.spans == [text_span_2]

    # 2d text doc
    text_doc_2 = text_docs[1]
    # reconstructed full text is as expected
    assert text_doc_2.text == "This is transcribed text number 3."
    # reference to original audio doc
    assert text_doc_2.audio_doc_id == audio_doc_2.id
    # mapping to audio spans in original doc
    text_span_3 = TextSpan(0, 34)
    assert text_doc_2.text_spans_to_audio_spans == {
        text_span_3: audio_span_3,
    }

    # has all expected segments
    text_segs_2 = text_doc_2.get_annotations_by_label(_TEXT_LABEL)
    assert len(text_segs_2) == len(audio_doc_2.get_annotations_by_label(_AUDIO_LABEL))


def test_prov():
    """Generated provenance nodes"""

    audio_span_1 = AudioSpan(0.0, 0.5)
    audio_span_2 = AudioSpan(1.0, 2.5)
    audio_doc = _get_audio_doc([audio_span_1, audio_span_2])

    doc_transcriber = DocTranscriber(
        input_label=_AUDIO_LABEL,
        output_label=_TEXT_LABEL,
        transcriber_func=_MockTranscriberFunction(),
    )
    prov_tracer = ProvTracer()
    doc_transcriber.set_prov_tracer(prov_tracer)
    text_doc = doc_transcriber.run([audio_doc])[0]
    text_segs = text_doc.get_annotations_by_label(_TEXT_LABEL)
    assert len(text_segs) == 2

    # data item id and operation id are correct
    text_seg_1 = text_segs[0]
    prov_1 = prov_tracer.get_prov(text_seg_1.id)
    assert prov_1.data_item == text_seg_1
    assert prov_1.op_desc == doc_transcriber.description

    # each text segment has corresponding voice segment as source
    audios_segs = audio_doc.get_annotations_by_label(_AUDIO_LABEL)
    audio_seg_1 = audios_segs[0]
    assert prov_1.source_data_items == [audio_seg_1]

    text_seg_2 = text_segs[1]
    prov_2 = prov_tracer.get_prov(text_seg_2.id)
    audio_seg_2 = audios_segs[1]
    assert prov_2.source_data_items == [audio_seg_2]


def test_attrs_to_copy():
    """Copying of audio segments attributes to text segments"""
    audio_span = AudioSpan(0.0, 0.5)

    audio_seg = _get_audio_segment(audio_span)
    # copied attribute
    audio_seg.add_attr(Attribute(label="speaker", value="Bob"))
    # uncopied attribute
    audio_seg.add_attr(Attribute(label="loud", value=True))

    audio_doc = AudioDocument()
    audio_doc.add_annotation(audio_seg)

    doc_transcriber = DocTranscriber(
        input_label=_AUDIO_LABEL,
        output_label=_TEXT_LABEL,
        transcriber_func=_MockTranscriberFunction(),
        attrs_to_copy=["speaker"],
    )
    text_doc = doc_transcriber.run([audio_doc])[0]
    text_seg = text_doc.get_annotations_by_label(_TEXT_LABEL)[0]
    # only negation attribute was copied
    speaker_attrs = text_seg.get_attrs_by_label("speaker")
    assert len(speaker_attrs) == 1 and speaker_attrs[0].value == "Bob"
    assert len(text_seg.get_attrs_by_label("loud")) == 0


class _CustomDocTranscriber(DocTranscriber):
    def augment_full_text_for_next_segment(
        self, full_text, segment_text, audio_segment
    ):
        # retrieve speaker name from audio segment attrs and include it in full text
        if len(full_text) > 0:
            full_text += "\n\n"
        speaker = audio_segment.get_attrs_by_label("speaker")[0].value
        full_text += f"- {speaker.upper()}:\n"
        return full_text


def test_custom_full_text():
    """Overriding of full text reconstruction method"""

    # audio doc with speaker name attributes on segments
    audio_doc = AudioDocument()
    audio_span_1 = AudioSpan(0.0, 0.5)
    audio_seg_1 = _get_audio_segment(audio_span_1)
    audio_seg_1.add_attr(Attribute(label="speaker", value="Bob"))
    audio_doc.add_annotation(audio_seg_1)
    audio_span_2 = AudioSpan(1.0, 2.5)
    audio_seg_2 = _get_audio_segment(audio_span_2)
    audio_seg_2.add_attr(Attribute(label="speaker", value="Alice"))
    audio_doc.add_annotation(audio_seg_2)

    doc_transcriber = _CustomDocTranscriber(
        input_label=_AUDIO_LABEL,
        output_label=_TEXT_LABEL,
        transcriber_func=_MockTranscriberFunction(),
    )
    text_doc = doc_transcriber.run([audio_doc])[0]

    expected_text = (
        "- BOB:\nThis is transcribed text number 1.\n\n- ALICE:\nThis is transcribed"
        " text number 2."
    )
    assert text_doc.text == expected_text


def test_store():
    """Overriding of full text reconstruction method"""

    # audio doc with explicitly provided shared store
    store = DictStore()
    audio_doc_1 = AudioDocument(store=store)
    audio_seg_1 = _get_audio_segment(AudioSpan(0.0, 0.5))
    audio_doc_1.add_annotation(audio_seg_1)
    # audio doc with own "private" store
    audio_doc_2 = AudioDocument()
    audio_seg_2 = _get_audio_segment(AudioSpan(0.0, 0.5))
    audio_doc_2.add_annotation(audio_seg_2)

    doc_transcriber = DocTranscriber(
        input_label=_AUDIO_LABEL,
        output_label=_TEXT_LABEL,
        transcriber_func=_MockTranscriberFunction(),
    )
    text_docs = doc_transcriber.run([audio_doc_1, audio_doc_2])

    # reuse same store for text doc when audio doc has public store
    text_doc_1 = text_docs[0]
    assert text_doc_1.store == audio_doc_1.store

    # use new store instance for text doc when audio doc has own private store
    text_doc_2 = text_docs[1]
    assert text_doc_2.store != audio_doc_2.store
