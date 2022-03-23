import re

from medkit.core import (
    Document,
    Annotation,
    Attribute,
    Origin,
    OperationDescription,
    ProcessingOperation,
)
from medkit.core.pipeline import Pipeline, PipelineStep


class _TextAnnotation(Annotation):
    """Mock text annotation"""

    def __init__(self, label: str, text: str):
        super().__init__(origin=Origin(), label=label)
        self.text = text


class _TextDocument(Document):
    """Mock text document"""

    def add_annotation(self, annotation: _TextAnnotation):
        super().add_annotation(annotation)


class _Uppercaser(ProcessingOperation):
    """Mock processing operation uppercasing annotations"""

    def __init__(self, output_label):
        self.output_label = output_label
        self._description = OperationDescription(name="Uppercaser")

    @property
    def description(self):
        return self._description

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
        self.output_label = output_label
        self.prefix = prefix
        self._description = OperationDescription(name="Prefixer")

    @property
    def description(self):
        return self._description

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
        self._description = OperationDescription(name="Splitter")

    @property
    def description(self):
        return self._description

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
        self._description = OperationDescription(name="Merger")

    @property
    def description(self):
        return self._description

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

        self._description = OperationDescription(name="KeywordMatcher")

    @property
    def description(self):
        return self._description

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
        self._description = OperationDescription(name="AttributeAdder")

    @property
    def description(self):
        return self._description

    def process(self, anns):
        for ann in anns:
            ann.attrs.append(
                Attribute(origin=Origin(), label=self.output_label, value=True)
            )


_SENTENCES = [
    "This is a sentence",
    "This is another sentence",
    "This is the last sentence",
]


def _get_doc():
    doc = _TextDocument()
    for text in _SENTENCES:
        ann = _TextAnnotation(label="sentence", text=text)
        doc.add_annotation(ann)
    return doc


def test_single_step():
    """Minimalist pipeline with only one step, retrieving input annotations from doc"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    sentence_anns = doc.get_annotations_by_label("sentence")
    # new annotations were added to the document
    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")
    assert len(uppercased_anns) == len(sentence_anns)
    # operation were added to the document
    assert doc.get_operations() == [uppercaser.description]
    # operation was properly called to generate new annotations
    assert [a.text.upper() for a in sentence_anns] == [a.text for a in uppercased_anns]


def test_multiple_steps():
    """Simple pipeline with 2 consecutive steps"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step_1)

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_uppercased_sentence", prefix=prefix)
    step_2 = PipelineStep(
        operation=prefixer,
        input_keys=["UPPERCASE"],
        output_keys=["PREFIX"],
    )
    pipeline.add_step(step_2)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    sentence_anns = doc.get_annotations_by_label("sentence")
    # new annotations were added to the document
    prefixed_uppercased_anns = doc.get_annotations_by_label(
        "prefixed_uppercased_sentence"
    )
    assert len(prefixed_uppercased_anns) == len(sentence_anns)
    # operation were added to the document
    assert doc.get_operations() == [uppercaser.description, prefixer.description]
    # operations were properly called and in the correct order to generate new annotations
    expected_texts = [prefix + a.text.upper() for a in sentence_anns]
    assert [a.text for a in prefixed_uppercased_anns] == expected_texts

    # intermediate annotations were also added to the document
    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")
    assert len(uppercased_anns) == len(sentence_anns)
    expected_texts = [a.text.upper() for a in uppercased_anns]
    assert [a.text for a in uppercased_anns] == expected_texts


def test_multiple_steps_with_same_output_key():
    """Pipeline with 2 step using the same output key, and another step
    using it as input"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    prefix_1 = "Hello! "
    prefixer_1 = _Prefixer(output_label="prefixed_sentence", prefix=prefix_1)
    step_1 = PipelineStep(
        operation=prefixer_1,
        input_keys=["SENTENCE"],
        output_keys=["PREFIX"],
    )
    pipeline.add_step(step_1)

    prefix_2 = "Hi! "
    prefixer_2 = _Prefixer(output_label="prefixed_sentence", prefix=prefix_2)
    step_2 = PipelineStep(
        operation=prefixer_2,
        input_keys=["SENTENCE"],
        output_keys=["PREFIX"],
    )
    pipeline.add_step(step_2)

    uppercaser = _Uppercaser(output_label="uppercased_prefixed_sentence")
    step_3 = PipelineStep(
        operation=uppercaser,
        input_keys=["PREFIX"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step_3)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_anns = doc.get_annotations_by_label("uppercased_prefixed_sentence")

    expected_texts = [(prefix_1 + a.text).upper() for a in sentence_anns] + [
        (prefix_2 + a.text).upper() for a in sentence_anns
    ]
    assert [a.text for a in uppercased_anns] == expected_texts


def test_multiple_steps_with_same_input_key():
    """Pipeline with 2 step using the same input key,
    which is also the output key of a previous step"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step_1)

    prefix_1 = "Hello! "
    prefixer_2 = _Prefixer(
        output_label="prefixed_uppercased_sentence_1", prefix=prefix_1
    )
    step_2 = PipelineStep(
        operation=prefixer_2,
        input_keys=["UPPERCASE"],
        output_keys=["PREFIX_1"],
    )
    pipeline.add_step(step_2)

    prefix_2 = "Hello! "
    prefixer_2 = _Prefixer(
        output_label="prefixed_uppercased_sentence_2", prefix=prefix_2
    )
    step_3 = PipelineStep(
        operation=prefixer_2,
        input_keys=["UPPERCASE"],
        output_keys=["PREFIX_2"],
    )
    pipeline.add_step(step_3)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    sentence_anns = doc.get_annotations_by_label("sentence")

    prefixed_uppercased_anns_1 = doc.get_annotations_by_label(
        "prefixed_uppercased_sentence_1"
    )
    expected_texts = [prefix_1 + a.text.upper() for a in sentence_anns]
    assert [a.text for a in prefixed_uppercased_anns_1] == expected_texts

    prefixed_uppercased_anns_2 = doc.get_annotations_by_label(
        "prefixed_uppercased_sentence_2"
    )
    expected_texts = [prefix_2 + a.text.upper() for a in sentence_anns]
    assert [a.text for a in prefixed_uppercased_anns_2] == expected_texts


def test_step_with_multiple_outputs():
    """Pipeline with a step having more than 1 output"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    splitter = _Splitter(output_label="split_sentence")
    step_1 = PipelineStep(
        operation=splitter,
        input_keys=["SENTENCE"],
        output_keys=["SPLIT_LEFT", "SPLIT_RIGHT"],
    )
    pipeline.add_step(step_1)

    uppercaser = _Uppercaser(output_label="uppercased_left_sentence")
    step_2 = PipelineStep(
        operation=uppercaser,
        input_keys=["SPLIT_LEFT"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step_2)

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_right_sentence", prefix=prefix)
    step_3 = PipelineStep(
        operation=prefixer,
        input_keys=["SPLIT_RIGHT"],
        output_keys=["PREFIX"],
    )
    pipeline.add_step(step_3)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_left_anns = doc.get_annotations_by_label("uppercased_left_sentence")
    prefixed_right_anns = doc.get_annotations_by_label("prefixed_right_sentence")

    expected_texts = [a.text[: len(a.text) // 2].upper() for a in sentence_anns]
    assert [a.text for a in uppercased_left_anns] == expected_texts

    expected_texts = [prefix + a.text[len(a.text) // 2 :] for a in sentence_anns]
    assert [a.text for a in prefixed_right_anns] == expected_texts


def test_step_with_multiple_inputs():
    """Pipeline with a step having more than 1 input"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step_1)

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_sentence", prefix=prefix)
    step_2 = PipelineStep(
        operation=prefixer,
        input_keys=["SENTENCE"],
        output_keys=["PREFIX"],
    )
    pipeline.add_step(step_2)

    merger = _Merger(output_label="merged_sentence")
    step_3 = PipelineStep(
        operation=merger,
        input_keys=["UPPERCASE", "PREFIX"],
        output_keys=["MERGE"],
    )
    pipeline.add_step(step_3)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    sentence_anns = doc.get_annotations_by_label("sentence")
    merged_anns = doc.get_annotations_by_label("merged_sentence")
    expected_texts = [a.text.upper() + prefix + a.text for a in sentence_anns]
    assert [a.text for a in merged_anns] == expected_texts


def test_step_with_no_output():
    """Pipeline with a step having no output, because it modifies the annotations
    it receives by adding attributes to them"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    attribute_adder = _AttributeAdder(output_label="validated")
    step_1 = PipelineStep(
        operation=attribute_adder,
        input_keys=["SENTENCE"],
        output_keys=[],
    )
    pipeline.add_step(step_1)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    sentence_anns = doc.get_annotations_by_label("sentence")
    for ann in sentence_anns:
        assert len(ann.attrs) == 1
        attr = ann.attrs[0]
        assert attr.label == "validated" and attr.value is True


def test_labels_for_input_key():
    """Pipeline with several label to input key associations,
    including2 labels associated to the same key"""
    doc = _get_doc()
    for text in [
        "This is a sentence with a different label",
        "This is another sentence with a different label",
    ]:
        doc.add_annotation(_TextAnnotation(label="alt_sentence", text=text))
    for text in ["Entity1", "Entity2"]:
        doc.add_annotation(_TextAnnotation(label="entity", text=text))

    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")
    pipeline.add_label_for_input_key(label="alt_sentence", key="SENTENCE")
    pipeline.add_label_for_input_key(label="entity", key="ENTITY")

    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step_1)

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_entity", prefix=prefix)
    step_2 = PipelineStep(
        operation=prefixer,
        input_keys=["ENTITY"],
        output_keys=["PREFIX"],
    )
    pipeline.add_step(step_2)

    pipeline.run_on_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    alt_sentence_anns = doc.get_annotations_by_label("alt_sentence")
    uppercased_sentence_anns = doc.get_annotations_by_label("uppercased_sentence")
    assert len(uppercased_sentence_anns) == len(sentence_anns) + len(alt_sentence_anns)

    expected_texts = [a.text.upper() for a in (sentence_anns + alt_sentence_anns)]
    assert [a.text for a in uppercased_sentence_anns] == expected_texts

    entity_anns = doc.get_annotations_by_label("entity")
    prefixed_entity_anns = doc.get_annotations_by_label("prefixed_entity")
    assert len(prefixed_entity_anns) == len(entity_anns)

    expected_texts = [prefix + a.text for a in entity_anns]
    assert [a.text for a in prefixed_entity_anns] == expected_texts


def test_step_with_different_output_length():
    """Simple pipeline with 2 consecutive steps. 1st step returns a number of annotations
    different from the number of annotations it received as input"""
    pipeline = Pipeline()
    pipeline.add_label_for_input_key(label="sentence", key="SENTENCE")

    keyword_matcher = _KeywordMatcher(
        output_label="entities", keywords=["sentence", "another"]
    )
    step_1 = PipelineStep(
        operation=keyword_matcher,
        input_keys=["SENTENCE"],
        output_keys=["KEYWORD_MATCH"],
    )
    pipeline.add_step(step_1)

    uppercaser = _Uppercaser(output_label="uppercased_entities")
    step_2 = PipelineStep(
        operation=uppercaser,
        input_keys=["KEYWORD_MATCH"],
        output_keys=["UPPERCASE"],
    )
    pipeline.add_step(step_2)

    doc = _get_doc()
    pipeline.run_on_doc(doc)

    entities = doc.get_annotations_by_label("uppercased_entities")
    assert len(entities) == 4
