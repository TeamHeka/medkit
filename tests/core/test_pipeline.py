import re

import pytest

from medkit.core import (
    generate_id,
    Document,
    Annotation,
    Attribute,
    ProcessingOperation,
    OperationDescription,
)
from medkit.core.pipeline import Pipeline, PipelineStep


class _TextAnnotation(Annotation):
    """Mock text annotation"""

    def __init__(self, label, text):
        super().__init__(label=label)
        self.text = text


_SENTENCES = [
    "This is a sentence",
    "This is another sentence",
    "This is the last sentence",
]


def _get_doc():
    doc = Document()
    for text in _SENTENCES:
        ann = _TextAnnotation(label="sentence", text=text)
        doc.add_annotation(ann)
    return doc


class _Uppercaser(ProcessingOperation):
    """Mock processing operation uppercasing annotations"""

    def __init__(self, output_label):
        self.id = generate_id()
        self.output_label = output_label

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Uppercaser")

    def process(self, anns):
        uppercase_anns = []
        for ann in anns:
            uppercase_ann = _TextAnnotation(
                label=self.output_label,
                text=ann.text.upper(),
            )
            uppercase_anns.append(uppercase_ann)
        return uppercase_anns


class _Prefixer(ProcessingOperation):
    """Mock processing operation prefixing annotations"""

    def __init__(self, output_label, prefix):
        self.id = generate_id()
        self.output_label = output_label
        self.prefix = prefix

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Prefixer")

    def process(self, anns):
        prefixed_anns = []
        for ann in anns:
            prefixed_ann = _TextAnnotation(
                label=self.output_label,
                text=self.prefix + ann.text,
            )
            prefixed_anns.append(prefixed_ann)
        return prefixed_anns


class _Splitter(ProcessingOperation):
    """Mock processing operation splitting annotations"""

    def __init__(self, output_label):
        self._output_label = output_label

    def process(self, anns):
        left_anns = []
        right_anns = []
        for ann in anns:
            half = len(ann.text) // 2
            left_ann = _TextAnnotation(label=self._output_label, text=ann.text[:half])
            left_anns.append(left_ann)
            right_ann = _TextAnnotation(label=self._output_label, text=ann.text[half:])
            right_anns.append(right_ann)
        return left_anns, right_anns


class _Merger(ProcessingOperation):
    """Mock processing operation merging annotations"""

    def __init__(self, output_label):
        self.output_label = output_label

    def process(self, left_anns, right_anns):
        merged_anns = []
        for left_ann, right_ann in zip(left_anns, right_anns):
            merged_ann = _TextAnnotation(
                label=self.output_label,
                text=left_ann.text + right_ann.text,
            )
            merged_anns.append(merged_ann)
        return merged_anns


class _KeywordMatcher(ProcessingOperation):
    """Mock processing operation finding exact keyword matches"""

    def __init__(self, output_label, keywords):
        self.output_label = output_label
        self.keywords = keywords

    def process(self, anns):
        entities = []
        for ann in anns:
            for keyword in self.keywords:
                match = re.search(keyword, ann.text)
                if match is None:
                    continue
                entity = _TextAnnotation(
                    label=self.output_label,
                    text=match.group(),
                )
                entities.append(entity)
        return entities


class _AttributeAdder(ProcessingOperation):
    """Mock processing operation adding attributes to existing annotations"""

    def __init__(self, output_label):
        self.output_label = output_label

    def process(self, anns):
        for ann in anns:
            ann.attrs.append(Attribute(label=self.output_label, value=True))


def test_single_step():
    """Minimalist pipeline with only one step"""
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    pipeline = Pipeline(
        steps=[step], input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_anns = pipeline.process(sentence_anns)

    # operation was properly called to generate new annotations
    assert [a.text.upper() for a in sentence_anns] == [a.text for a in uppercased_anns]

    # new annotations were added to the document
    assert doc.get_annotations_by_label("uppercased_sentence") == uppercased_anns
    # operation were added to the document
    assert doc.get_operations() == [uppercaser.description]


def test_multiple_steps():
    """Simple pipeline with 2 consecutive steps"""
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_uppercased_sentence", prefix=prefix)
    step_2 = PipelineStep(
        operation=prefixer,
        input_keys=["UPPERCASE"],
        output_keys=["PREFIX"],
    )

    pipeline = Pipeline(
        steps=[step_1, step_2], input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    prefixed_uppercased_anns = pipeline.process(sentence_anns)

    # operations were properly called and in the correct order to generate new annotations
    expected_texts = [prefix + a.text.upper() for a in sentence_anns]
    assert [a.text for a in prefixed_uppercased_anns] == expected_texts

    # new annotations were added to the document
    assert (
        doc.get_annotations_by_label("prefixed_uppercased_sentence")
        == prefixed_uppercased_anns
    )
    # intermediate annotations were also added to the document
    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")
    assert len(uppercased_anns) == len(sentence_anns)
    expected_texts = [a.text.upper() for a in uppercased_anns]
    assert [a.text for a in uppercased_anns] == expected_texts

    # operation were added to the document
    assert doc.get_operations() == [uppercaser.description, prefixer.description]


def test_multiple_steps_with_same_output_key():
    """Pipeline with 2 step using the same output key, and another step
    using it as input"""
    prefix_1 = "Hello! "
    prefixer_1 = _Prefixer(output_label="prefixed_sentence", prefix=prefix_1)
    step_1 = PipelineStep(
        operation=prefixer_1,
        input_keys=["SENTENCE"],
        output_keys=["PREFIX"],
    )

    prefix_2 = "Hi! "
    prefixer_2 = _Prefixer(output_label="prefixed_sentence", prefix=prefix_2)
    step_2 = PipelineStep(
        operation=prefixer_2,
        input_keys=["SENTENCE"],
        output_keys=["PREFIX"],
    )

    uppercaser = _Uppercaser(output_label="uppercased_prefixed_sentence")
    step_3 = PipelineStep(
        operation=uppercaser,
        input_keys=["PREFIX"],
        output_keys=["UPPERCASE"],
    )

    pipeline = Pipeline(
        steps=[step_1, step_2, step_3],
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_anns = pipeline.process(sentence_anns)

    # operations were properly called in the correct order
    expected_texts = [(prefix_1 + a.text).upper() for a in sentence_anns] + [
        (prefix_2 + a.text).upper() for a in sentence_anns
    ]
    assert [a.text for a in uppercased_anns] == expected_texts


def test_multiple_steps_with_same_input_key():
    """Pipeline with 2 step using the same input key,
    which is also the output key of a previous step"""
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    prefix_1 = "Hello! "
    prefixer_2 = _Prefixer(
        output_label="prefixed_uppercased_sentence_1", prefix=prefix_1
    )
    step_2 = PipelineStep(
        operation=prefixer_2,
        input_keys=["UPPERCASE"],
        output_keys=["PREFIX_1"],
    )

    prefix_2 = "Hello! "
    prefixer_2 = _Prefixer(
        output_label="prefixed_uppercased_sentence_2", prefix=prefix_2
    )
    step_3 = PipelineStep(
        operation=prefixer_2,
        input_keys=["UPPERCASE"],
        output_keys=["PREFIX_2"],
    )

    pipeline = Pipeline(
        steps=[step_1, step_2, step_3],
        input_keys=["SENTENCE"],
        output_keys=["PREFIX_1", "PREFIX_2"],
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    prefixed_uppercased_anns_1, prefixed_uppercased_anns_2 = pipeline.process(
        sentence_anns
    )

    # operations were properly called in the correct order
    expected_texts_1 = [prefix_1 + a.text.upper() for a in sentence_anns]
    assert [a.text for a in prefixed_uppercased_anns_1] == expected_texts_1
    expected_texts_2 = [prefix_2 + a.text.upper() for a in sentence_anns]
    assert [a.text for a in prefixed_uppercased_anns_2] == expected_texts_2


def test_step_with_multiple_outputs():
    """Pipeline with a step having more than 1 output"""
    splitter = _Splitter(output_label="split_sentence")
    step_1 = PipelineStep(
        operation=splitter,
        input_keys=["SENTENCE"],
        output_keys=["SPLIT_LEFT", "SPLIT_RIGHT"],
    )

    uppercaser = _Uppercaser(output_label="uppercased_left_sentence")
    step_2 = PipelineStep(
        operation=uppercaser,
        input_keys=["SPLIT_LEFT"],
        output_keys=["UPPERCASE"],
    )

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_right_sentence", prefix=prefix)
    step_3 = PipelineStep(
        operation=prefixer,
        input_keys=["SPLIT_RIGHT"],
        output_keys=["PREFIX"],
    )

    pipeline = Pipeline(
        steps=[step_1, step_2, step_3],
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE", "PREFIX"],
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_left_anns, prefixed_right_anns = pipeline.process(sentence_anns)

    # operations were properly called in the correct order
    expected_texts = [a.text[: len(a.text) // 2].upper() for a in sentence_anns]
    assert [a.text for a in uppercased_left_anns] == expected_texts
    expected_texts = [prefix + a.text[len(a.text) // 2 :] for a in sentence_anns]
    assert [a.text for a in prefixed_right_anns] == expected_texts


def test_step_with_multiple_inputs():
    """Pipeline with a step having more than 1 input"""
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_sentence", prefix=prefix)
    step_2 = PipelineStep(
        operation=prefixer,
        input_keys=["SENTENCE"],
        output_keys=["PREFIX"],
    )

    merger = _Merger(output_label="merged_sentence")
    step_3 = PipelineStep(
        operation=merger,
        input_keys=["UPPERCASE", "PREFIX"],
        output_keys=["MERGE"],
    )

    pipeline = Pipeline(
        steps=[step_1, step_2, step_3], input_keys=["SENTENCE"], output_keys=["MERGE"]
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    merged_anns = pipeline.process(sentence_anns)

    # operations were properly called in the correct order
    expected_texts = [a.text.upper() + prefix + a.text for a in sentence_anns]
    assert [a.text for a in merged_anns] == expected_texts


def test_step_with_no_output():
    """Pipeline with a step having no output, because it modifies the annotations
    it receives by adding attributes to them"""
    attribute_adder = _AttributeAdder(output_label="validated")
    step_1 = PipelineStep(
        operation=attribute_adder,
        input_keys=["SENTENCE"],
        output_keys=[],
    )

    pipeline = Pipeline(steps=[step_1], input_keys=["SENTENCE"], output_keys=[])

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    pipeline.process(sentence_anns)

    # make sure attributes were added
    for ann in sentence_anns:
        assert len(ann.attrs) == 1
        attr = ann.attrs[0]
        assert attr.label == "validated" and attr.value is True


def test_step_with_different_output_length():
    """Simple pipeline with 2 consecutive steps. 1st step returns a number of annotations
    different from the number of annotations it received as input"""
    keyword_matcher = _KeywordMatcher(
        output_label="entities", keywords=["sentence", "another"]
    )
    step_1 = PipelineStep(
        operation=keyword_matcher,
        input_keys=["SENTENCE"],
        output_keys=["KEYWORD_MATCH"],
    )

    uppercaser = _Uppercaser(output_label="uppercased_entities")
    step_2 = PipelineStep(
        operation=uppercaser,
        input_keys=["KEYWORD_MATCH"],
        output_keys=["UPPERCASE"],
    )

    pipeline = Pipeline(
        steps=[step_1, step_2], input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    entities = pipeline.process(sentence_anns)
    assert len(entities) == 4
    assert len(doc.get_annotations_by_label("uppercased_entities")) == len(entities)


def test_nested_pipeline():
    """Pipeline with a step that is also a pipeline"""
    # build inner pipeline
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    sub_step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    prefix_1 = "Hi! "
    prefixer_1 = _Prefixer(output_label="prefixed_uppercased_sentence", prefix=prefix_1)
    sub_step_2 = PipelineStep(
        operation=prefixer_1,
        input_keys=["UPPERCASE"],
        output_keys=["PREFIX"],
    )

    sub_pipeline = Pipeline(
        steps=[sub_step_1, sub_step_2], input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )

    # build main pipeline
    prefix_2 = "Hello! "
    prefixer_2 = _Prefixer(output_label="prefixed_sentence", prefix=prefix_2)
    step_1 = PipelineStep(
        operation=prefixer_2,
        input_keys=["SENTENCE"],
        output_keys=["PREFIX"],
    )

    step_2 = PipelineStep(
        operation=sub_pipeline,
        input_keys=["PREFIX"],
        output_keys=["SUB_PIPELINE"],
    )

    pipeline = Pipeline(
        steps=[step_1, step_2],
        input_keys=["SENTENCE"],
        output_keys=["SUB_PIPELINE"],
    )

    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    output_anns = pipeline.process(sentence_anns)

    # operations were properly called and in the correct order to generate new annotations
    expected_texts = [prefix_1 + (prefix_2 + a.text).upper() for a in sentence_anns]
    assert [a.text for a in output_anns] == expected_texts

    # new annotations were added to the document
    assert doc.get_annotations_by_label("prefixed_uppercased_sentence") == output_anns
    # intermediate annotations were also added to the document
    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")
    assert len(uppercased_anns) == len(sentence_anns)
    prefixed_uppercased_anns = doc.get_annotations_by_label(
        "prefixed_uppercased_sentence"
    )
    assert len(prefixed_uppercased_anns) == len(sentence_anns)

    # operations were added to the document
    assert doc.get_operations() == [
        prefixer_2.description,
        uppercaser.description,
        prefixer_1.description,
        sub_pipeline.description,
    ]


def test_sanity_check():
    """Sanity checks"""
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    prefixer = _Prefixer(output_label="prefixed_uppercased_sentence", prefix="prefix ")

    steps_1 = [
        PipelineStep(uppercaser, input_keys=["SENTENCE"], output_keys=["UPPERCASE"]),
        PipelineStep(prefixer, input_keys=["UPPERCASE"], output_keys=["PREFIX"]),
    ]

    # valid pipeline should not raise
    pipeline_1 = Pipeline(
        steps=steps_1, input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )
    pipeline_1.check_sanity()

    # pipeline input key not corresponding to any step input key
    pipeline_2 = Pipeline(
        steps=steps_1, input_keys=["WRONG_KEY"], output_keys=["PREFIX"]
    )
    with pytest.raises(
        Exception,
        match="Pipeline input key WRONG_KEY does not correspond to any step input key",
    ):
        pipeline_2.check_sanity()

    # pipeline output key not corresponding to any step input key
    pipeline_3 = Pipeline(
        steps=steps_1, input_keys=["SENTENCE"], output_keys=["WRONG_KEY"]
    )
    with pytest.raises(
        Exception,
        match=(
            "Pipeline output key WRONG_KEY does not correspond to any step output key"
        ),
    ):
        pipeline_3.check_sanity()

    # step input key not corresponding to any step or pipeline input key
    steps_2 = [
        PipelineStep(uppercaser, input_keys=["SENTENCE"], output_keys=["UPPERCASE"]),
        PipelineStep(prefixer, input_keys=["WRONG_KEY"], output_keys=["PREFIX"]),
    ]
    pipeline_4 = Pipeline(
        steps=steps_2, input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )
    with pytest.raises(
        Exception,
        match=(
            "Step input key WRONG_KEY does not correspond to any step output key nor"
            " any pipeline input key"
        ),
    ):
        pipeline_4.check_sanity()

    # step input key not available yet
    steps_3 = list(reversed(steps_1))
    pipeline_5 = Pipeline(
        steps=steps_3, input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )
    with pytest.raises(
        Exception, match="Step input key UPPERCASE is not available yet at this step"
    ):
        pipeline_5.check_sanity()
