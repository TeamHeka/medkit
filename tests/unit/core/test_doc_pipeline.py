from medkit.core import (
    generate_id,
    Document,
    Annotation,
    Attribute,
    Pipeline,
    PipelineStep,
    OperationDescription,
)
from medkit.core.doc_pipeline import DocPipeline


_SENTENCES = [
    "This is a sentence",
    "This is another sentence",
    "This is the last sentence",
]


class _TextAnnotation(Annotation):
    """Mock text annotation"""

    def __init__(self, label, text):
        super().__init__(label=label)
        self.text = text


def _get_doc():
    doc = Document()
    for text in _SENTENCES:
        ann = _TextAnnotation(label="sentence", text=text)
        doc.add_annotation(ann)
    return doc


class _Uppercaser:
    """Mock processing operation uppercasing annotations"""

    def __init__(self, output_label):
        self.id = generate_id()
        self.output_label = output_label

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Uppercaser")

    def run(self, anns):
        uppercase_anns = []
        for ann in anns:
            uppercase_ann = _TextAnnotation(
                label=self.output_label,
                text=ann.text.upper(),
            )
            uppercase_anns.append(uppercase_ann)
        return uppercase_anns


class _Prefixer:
    """Mock processing operation prefixing annotations"""

    def __init__(self, output_label, prefix):
        self.id = generate_id()
        self.output_label = output_label
        self.prefix = prefix

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Prefixer")

    def run(self, anns):
        prefixed_anns = []
        for ann in anns:
            prefixed_ann = _TextAnnotation(
                label=self.output_label,
                text=self.prefix + ann.text,
            )
            prefixed_anns.append(prefixed_ann)
        return prefixed_anns


class _AttributeAdder:
    """Mock processing operation adding attributes to existing annotations"""

    def __init__(self, output_label):
        self.id = generate_id()
        self.output_label = output_label

    @property
    def description(self):
        return OperationDescription(id=self.id, name="AttributeAdder")

    def run(self, anns):
        for ann in anns:
            ann.attrs.append(Attribute(label=self.output_label, value=True))


def test_single_step():
    """Minimalist doc pipeline with only one step, retrieving input annotations from doc
    """
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )
    pipeline = Pipeline(
        steps=[step],
        input_keys=step.input_keys,
        output_keys=step.output_keys,
    )
    doc_pipeline = DocPipeline(
        pipeline=pipeline, labels_by_input_key={"SENTENCE": ["sentence"]}
    )

    doc = _get_doc()
    doc_pipeline.run([doc])

    sentence_anns = doc.get_annotations_by_label("sentence")

    # new annotations were added to the document
    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")

    # operation was properly called to generate new annotations
    assert [a.text.upper() for a in sentence_anns] == [a.text for a in uppercased_anns]


def test_multiple_steps():
    """Simple pipeline doc with 2 consecutive steps"""
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
        steps=[step_1, step_2],
        input_keys=step_1.input_keys,
        output_keys=step_2.output_keys,
    )

    doc_pipeline = DocPipeline(
        pipeline=pipeline, labels_by_input_key={"SENTENCE": ["sentence"]}
    )
    doc = _get_doc()
    doc_pipeline.run([doc])

    sentence_anns = doc.get_annotations_by_label("sentence")

    # new annotations were added to the document
    prefixed_uppercased_anns = doc.get_annotations_by_label(
        "prefixed_uppercased_sentence"
    )
    assert len(prefixed_uppercased_anns) == len(sentence_anns)

    # operations were properly called and in the correct order to generate new annotations
    expected_texts = [prefix + a.text.upper() for a in sentence_anns]
    assert [a.text for a in prefixed_uppercased_anns] == expected_texts


def test_no_output():
    """Doc pipeline having no output, because it has an operation that
    modifies the annotations it receives by adding attributes to them"""
    attribute_adder = _AttributeAdder(output_label="validated")
    step_1 = PipelineStep(
        operation=attribute_adder,
        input_keys=["SENTENCE"],
        output_keys=[],
    )

    pipeline = Pipeline(steps=[step_1], input_keys=step_1.input_keys, output_keys=[])

    doc_pipeline = DocPipeline(
        pipeline=pipeline, labels_by_input_key={"SENTENCE": ["sentence"]}
    )
    doc = _get_doc()
    doc_pipeline.run([doc])

    sentence_anns = doc.get_annotations_by_label("sentence")
    for ann in sentence_anns:
        assert len(ann.attrs) == 1
        attr = ann.attrs[0]
        assert attr.label == "validated" and attr.value is True


def test_multiple_outputs():
    """Doc pipeline with more than 1 output"""
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

    pipeline = Pipeline(
        steps=[step_1, step_2],
        input_keys=step_1.input_keys,
        output_keys=step_1.output_keys + step_2.output_keys,
    )

    doc_pipeline = DocPipeline(
        pipeline=pipeline, labels_by_input_key={"SENTENCE": ["sentence"]}
    )
    doc = _get_doc()
    doc_pipeline.run([doc])

    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")
    prefixed_anns = doc.get_annotations_by_label("prefixed_sentence")

    expected_texts = [a.text.upper() for a in sentence_anns]
    assert [a.text for a in uppercased_anns] == expected_texts

    expected_texts = [prefix + a.text for a in sentence_anns]
    assert [a.text for a in prefixed_anns] == expected_texts


def test_labels_for_input_key():
    """Doc pipeline with several label to input key associations,
    including 2 labels associated to the same key"""
    doc = _get_doc()
    for text in [
        "This is a sentence with a different label",
        "This is another sentence with a different label",
    ]:
        doc.add_annotation(_TextAnnotation(label="alt_sentence", text=text))
    for text in ["Entity1", "Entity2"]:
        doc.add_annotation(_TextAnnotation(label="entity", text=text))

    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    prefix = "Hello! "
    prefixer = _Prefixer(output_label="prefixed_entity", prefix=prefix)
    step_2 = PipelineStep(
        operation=prefixer,
        input_keys=["ENTITY"],
        output_keys=["PREFIX"],
    )

    labels_by_input_key = {
        "SENTENCE": ["sentence", "alt_sentence"],
        "ENTITY": ["entity"],
    }

    pipeline = Pipeline(
        steps=[step_1, step_2],
        input_keys=step_1.input_keys + step_2.input_keys,
        output_keys=step_1.output_keys + step_2.output_keys,
    )

    doc_pipeline = DocPipeline(
        pipeline=pipeline,
        labels_by_input_key=labels_by_input_key,
    )
    doc_pipeline.run([doc])
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


def test_nested_pipeline():
    """DocPipeline wrapped in a Pipeline"""
    # build inner pipeline
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    sub_step = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    sub_pipeline = Pipeline(
        steps=[sub_step],
        input_keys=sub_step.input_keys,
        output_keys=sub_step.output_keys,
    )
    doc_sub_pipeline = DocPipeline(
        pipeline=sub_pipeline, labels_by_input_key={"SENTENCE": ["sentence"]}
    )

    # wrap it in main pipeline
    step = PipelineStep(
        operation=doc_sub_pipeline,
        input_keys=["DOC"],
        output_keys=[],
    )

    pipeline = Pipeline(steps=[step], input_keys=["DOC"], output_keys=[])

    doc = _get_doc()
    pipeline.run([doc])
    sentence_anns = doc.get_annotations_by_label("sentence")
    # new annotations were added to the document
    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")
    # operation was properly called to generate new annotations
    assert [a.text.upper() for a in sentence_anns] == [a.text for a in uppercased_anns]


def test_key_group():
    """Doc pipeline with keys group for annotation"""
    uppercaser = _Uppercaser(output_label="uppercased_sentence")
    step = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    pipeline = Pipeline(
        [step],
        input_keys=step.input_keys,
        output_keys=step.output_keys,
    )

    doc_pipeline = DocPipeline(
        pipeline=pipeline, labels_by_input_key={"SENTENCE": ["sentence"]}
    )
    doc = _get_doc()
    doc_pipeline.run([doc])

    uppercased_anns = doc.get_annotations_by_label("uppercased_sentence")
    for ann in uppercased_anns:
        assert ann.keys == {"UPPERCASE"}
