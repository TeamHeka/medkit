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
from medkit.core.prov_builder import ProvBuilder


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
        self._prov_builder = None

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Uppercaser")

    def set_prov_builder(self, prov_builder):
        self._prov_builder = prov_builder

    def process(self, anns):
        uppercase_anns = []
        for ann in anns:
            uppercase_ann = _TextAnnotation(
                label=self.output_label, text=ann.text.upper()
            )
            uppercase_anns.append(uppercase_ann)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    uppercase_ann.id, self.description.id, source_ids=[ann.id]
                )
        return uppercase_anns


class _Prefixer(ProcessingOperation):
    """Mock processing operation prefixing annotations"""

    def __init__(self, prefix, output_label):
        self.id = generate_id()
        self.output_label = output_label
        self.prefix = prefix

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Prefixer")

    def set_prov_builder(self, prov_builder):
        self._prov_builder = prov_builder

    def process(self, anns):
        prefixed_anns = []
        for ann in anns:
            prefixed_ann = _TextAnnotation(
                label=self.output_label, text=self.prefix + ann.text
            )
            prefixed_anns.append(prefixed_ann)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    prefixed_ann.id, self.description.id, source_ids=[ann.id]
                )
        return prefixed_anns


class _AttributeAdder(ProcessingOperation):
    """Mock processing operation adding attributes to existing annotations"""

    def __init__(self, output_label):
        self.id = generate_id()
        self.output_label = output_label

    @property
    def description(self):
        return OperationDescription(id=self.id, name="AttributeAdder")

    def set_prov_builder(self, prov_builder):
        self._prov_builder = prov_builder

    def process(self, anns):
        for ann in anns:
            attr = Attribute(label=self.output_label, value=True)
            ann.attrs.append(attr)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    attr.id, self.description.id, source_ids=[ann.id]
                )


def test_single_step():
    """Minimalist pipeline with only one step"""
    uppercaser = _Uppercaser(output_label="uppercased_prefixed_sentence")
    step = PipelineStep(
        operation=uppercaser, input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    pipeline = Pipeline(
        steps=[step], input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    prov_builder = ProvBuilder()
    pipeline.set_prov_builder(prov_builder)
    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_anns = pipeline.process(sentence_anns)
    assert len(uppercased_anns) == len(sentence_anns)

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for uppercased_ann, sentence_ann in zip(uppercased_anns, sentence_anns):
        uppercased_node = graph.get_node(uppercased_ann.id)
        # operation id is of outer pipeline operation
        assert uppercased_node.operation_id == pipeline.id
        # uppercased node has corresponding sentence ann as source
        assert len(uppercased_node.source_ids) == 1
        assert uppercased_node.source_ids == [sentence_ann.id]

        # sentence node is a stub node (no operation, no source)
        sentence_node = graph.get_node(sentence_ann.id)
        assert sentence_node.operation_id is None
        assert not sentence_node.source_ids

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)

    for uppercased_ann, sentence_ann in zip(uppercased_anns, sentence_anns):
        uppercased_node = sub_graph.get_node(uppercased_ann.id)
        # operation id is of inner uppercaser operation
        assert uppercased_node.operation_id == uppercaser.id
        # uppercased node has corresponding sentence ann as source
        assert len(uppercased_node.source_ids) == 1
        assert uppercased_node.source_ids == [sentence_ann.id]

        # sentence node is a stub node (no operation, no source)
        sentence_node = sub_graph.get_node(sentence_ann.id)
        assert sentence_node.operation_id is None
        assert not sentence_node.source_ids


def test_multiple_steps():
    """Simple pipeline with 2 consecutive steps"""
    prefixer = _Prefixer(prefix="Hello! ", output_label="prefixed_sentence")
    step_1 = PipelineStep(
        operation=prefixer, input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )

    uppercaser = _Uppercaser(output_label="uppercased_prefixed_sentence")
    step_2 = PipelineStep(
        operation=uppercaser, input_keys=["PREFIX"], output_keys=["UPPERCASE"]
    )

    pipeline = Pipeline(
        steps=[step_1, step_2], input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    prov_builder = ProvBuilder()
    pipeline.set_prov_builder(prov_builder)
    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_anns = pipeline.process(sentence_anns)
    assert len(uppercased_anns) == len(sentence_anns)

    graph = prov_builder.graph
    graph.check_sanity()

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for uppercased_ann, sentence_ann in zip(uppercased_anns, sentence_anns):
        uppercased_node = graph.get_node(uppercased_ann.id)
        # operation id is of pipeline operation
        assert uppercased_node.operation_id == pipeline.id
        # uppercased node has corresponding sentence as source
        assert uppercased_node.source_ids == [sentence_ann.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)

    for uppercased_ann, sentence_ann in zip(uppercased_anns, sentence_anns):
        uppercased_node = sub_graph.get_node(uppercased_ann.id)
        # operation id is of inner uppercaser operation
        assert uppercased_node.operation_id == uppercaser.id
        # uppercased node has corresponding prefixed ann as source
        assert len(uppercased_node.source_ids) == 1
        prefixed_ann_id = uppercased_node.source_ids[0]

        prefixed_node = sub_graph.get_node(prefixed_ann_id)
        # operation id is of inner prefixer operation
        assert prefixed_node.operation_id == prefixer.id
        # prefixed node has corresponding sentence as source
        assert prefixed_node.source_ids == [sentence_ann.id]


@pytest.mark.xfail
def test_step_with_attributes():
    """Pipeline with a step adding attributes to existing annotations instead of returning new annotations"""
    prefixer = _Prefixer(prefix="Hello! ", output_label="prefixed_sentence")
    step_1 = PipelineStep(
        operation=prefixer, input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )

    uppercaser = _Uppercaser(output_label="uppercased_prefixed_sentence")
    step_2 = PipelineStep(
        operation=uppercaser, input_keys=["PREFIX"], output_keys=["UPPERCASE"]
    )

    attribute_adder = _AttributeAdder(output_label="validated")
    step_3 = PipelineStep(
        operation=attribute_adder, input_keys=["UPPERCASE"], output_keys=[]
    )

    pipeline = Pipeline(
        steps=[step_1, step_2, step_3],
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    prov_builder = ProvBuilder()
    pipeline.set_prov_builder(prov_builder)
    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    uppercased_anns = pipeline.process(sentence_anns)
    assert len(uppercased_anns) == len(sentence_anns)

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for uppercased_ann, sentence_ann in zip(uppercased_anns, sentence_anns):
        assert len(uppercased_ann.attrs) == 1
        attr = uppercased_ann.attrs[0]
        # FIXME currently failing, attributes created in pipeline are not added to outer main graph
        attr_node = graph.get_node(attr.id)
        # operation id is of outer pipeline operation
        assert attr_node.operation_id == pipeline.id
        # attribute node has corresponding sentence ann as source
        # (because it is what was given as input to the pipeline operation)
        assert attr_node.source_ids == [sentence_ann.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)

    for uppercased_ann in uppercased_anns:
        assert len(uppercased_ann.attrs) == 1
        attr = uppercased_ann.attrs[0]
        attr_node = sub_graph.get_node(attr.id)
        # operation id is of inner attribute adder operation
        assert attr_node.operation_id == attribute_adder.id
        # attribute node has corresponding uppercased ann as source
        assert attr_node.source_ids == [uppercased_ann.id]


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

    prov_builder = ProvBuilder()
    pipeline.set_prov_builder(prov_builder)
    doc = _get_doc()
    pipeline.set_doc(doc)
    sentence_anns = doc.get_annotations_by_label("sentence")
    output_anns = pipeline.process(sentence_anns)
    assert len(output_anns) == len(sentence_anns)

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for output_ann, sentence_ann in zip(output_anns, sentence_anns):
        output_node = graph.get_node(output_ann.id)
        # operation id is of main pipeline operation
        assert output_node.operation_id == pipeline.id
        # uppercased node has corresponding sentence as source
        assert output_node.source_ids == [sentence_ann.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)
    for output_ann, sentence_ann in zip(output_anns, sentence_anns):
        # node for result of sub pipeline
        node = sub_graph.get_node(output_ann.id)
        assert node.operation_id == sub_pipeline.id

        # node for result of prefixer before sub pipeline
        node = sub_graph.get_node(node.source_ids[0])
        assert node.operation_id == prefixer_2.id
        assert len(node.source_ids) == 1

        # stub node for input sentence ann
        node = sub_graph.get_node(node.source_ids[0])
        assert node.data_item_id == sentence_ann.id
        assert node.operation_id is None
        assert not node.source_ids

    # check innermost sub graph
    sub_graph = sub_graph.get_sub_graph(sub_pipeline.id)
    for output_ann, sentence_ann in zip(output_anns, sentence_anns):
        # node for result of prefixer inside sub pipeline
        node = sub_graph.get_node(output_ann.id)
        assert node.operation_id == prefixer_1.id
        assert len(node.source_ids) == 1

        # node for result of uppercaser inside sub pipeline
        node = sub_graph.get_node(node.source_ids[0])
        assert node.operation_id == uppercaser.id
        assert len(node.source_ids) == 1

        # stub node for result of prefixer before sub pipeline
        node = sub_graph.get_node(node.source_ids[0])
        assert node.operation_id is None
        assert not node.source_ids
