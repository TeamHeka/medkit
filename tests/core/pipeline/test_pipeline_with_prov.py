from medkit.core import generate_id, OperationDescription
from medkit.core.pipeline import Pipeline, PipelineStep
from medkit.core.prov_builder import ProvBuilder


class _Segment:
    """Mock text segment"""

    def __init__(self, text):
        self.id = generate_id()
        self.text = text
        self.attrs = []


class _Attribute:
    """Mock attribute"""

    def __init__(self, label, value):
        self.id = generate_id()
        self.label = label
        self.value = value


_SENTENCES = [
    "This is a sentence",
    "This is another sentence",
    "This is the last sentence",
]


def _get_sentence_segments():
    return [_Segment(text=text) for text in _SENTENCES]


class _Uppercaser:
    """Mock processing operation uppercasing segments"""

    def __init__(self):
        self.id = generate_id()
        self._prov_builder = None

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Uppercaser")

    def set_prov_builder(self, prov_builder):
        self._prov_builder = prov_builder

    def process(self, segments):
        uppercase_segments = []
        for segment in segments:
            uppercase_segment = _Segment(segment.text.upper())
            uppercase_segments.append(uppercase_segment)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    uppercase_segment, self.description, source_data_items=[segment]
                )
        return uppercase_segments


class _Prefixer:
    """Mock processing operation prefixing segments"""

    def __init__(self, prefix):
        self.id = generate_id()
        self.prefix = prefix

    @property
    def description(self):
        return OperationDescription(id=self.id, name="Prefixer")

    def set_prov_builder(self, prov_builder):
        self._prov_builder = prov_builder

    def process(self, segments):
        prefixed_segments = []
        for segment in segments:
            prefixed_segment = _Segment(self.prefix + segment.text)
            prefixed_segments.append(prefixed_segment)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    prefixed_segment, self.description, source_data_items=[segment]
                )
        return prefixed_segments


class _AttributeAdder:
    """Mock processing operation adding attributes to existing segments"""

    def __init__(self, label):
        self.id = generate_id()
        self.label = label

    @property
    def description(self):
        return OperationDescription(id=self.id, name="AttributeAdder")

    def set_prov_builder(self, prov_builder):
        self._prov_builder = prov_builder

    def process(self, segments):
        for segment in segments:
            attr = _Attribute(label=self.label, value=True)
            segment.attrs.append(attr)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    attr, self.description, source_data_items=[segment]
                )


def test_single_step():
    """Minimalist pipeline with only one step"""
    uppercaser = _Uppercaser()
    step = PipelineStep(
        operation=uppercaser, input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    pipeline = Pipeline(
        steps=[step], input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    prov_builder = ProvBuilder()
    pipeline.set_prov_builder(prov_builder)
    sentence_segs = _get_sentence_segments()
    uppercased_segs = pipeline.process(sentence_segs)
    assert len(uppercased_segs) == len(sentence_segs)

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for uppercased_seg, sentence_seg in zip(uppercased_segs, sentence_segs):
        uppercased_node = graph.get_node(uppercased_seg.id)
        # operation id is of outer pipeline operation
        assert uppercased_node.operation_id == pipeline.id
        # uppercased node has corresponding sentence segment as source
        assert len(uppercased_node.source_ids) == 1
        assert uppercased_node.source_ids == [sentence_seg.id]

        # sentence node is a stub node (no operation, no source)
        sentence_node = graph.get_node(sentence_seg.id)
        assert sentence_node.operation_id is None
        assert not sentence_node.source_ids

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)

    for uppercased_seg, sentence_seg in zip(uppercased_segs, sentence_segs):
        uppercased_node = sub_graph.get_node(uppercased_seg.id)
        # operation id is of inner uppercaser operation
        assert uppercased_node.operation_id == uppercaser.id
        # uppercased node has corresponding sentence segment as source
        assert len(uppercased_node.source_ids) == 1
        assert uppercased_node.source_ids == [sentence_seg.id]

        # sentence node is a stub node (no operation, no source)
        sentence_node = sub_graph.get_node(sentence_seg.id)
        assert sentence_node.operation_id is None
        assert not sentence_node.source_ids


def test_multiple_steps():
    """Simple pipeline with 2 consecutive steps"""
    prefixer = _Prefixer(prefix="Hello! ")
    step_1 = PipelineStep(
        operation=prefixer, input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )

    uppercaser = _Uppercaser()
    step_2 = PipelineStep(
        operation=uppercaser, input_keys=["PREFIX"], output_keys=["UPPERCASE"]
    )

    pipeline = Pipeline(
        steps=[step_1, step_2], input_keys=["SENTENCE"], output_keys=["UPPERCASE"]
    )

    prov_builder = ProvBuilder()
    pipeline.set_prov_builder(prov_builder)
    sentence_segs = _get_sentence_segments()
    uppercased_segs = pipeline.process(sentence_segs)
    assert len(uppercased_segs) == len(sentence_segs)

    graph = prov_builder.graph
    graph.check_sanity()

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for uppercased_seg, sentence_seg in zip(uppercased_segs, sentence_segs):
        uppercased_node = graph.get_node(uppercased_seg.id)
        # operation id is of pipeline operation
        assert uppercased_node.operation_id == pipeline.id
        # uppercased node has corresponding sentence as source
        assert uppercased_node.source_ids == [sentence_seg.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)

    for uppercased_seg, sentence_seg in zip(uppercased_segs, sentence_segs):
        uppercased_node = sub_graph.get_node(uppercased_seg.id)
        # operation id is of inner uppercaser operation
        assert uppercased_node.operation_id == uppercaser.id
        # uppercased node has corresponding prefixed segment as source
        assert len(uppercased_node.source_ids) == 1
        prefixed_seg_id = uppercased_node.source_ids[0]

        prefixed_node = sub_graph.get_node(prefixed_seg_id)
        # operation id is of inner prefixer operation
        assert prefixed_node.operation_id == prefixer.id
        # prefixed node has corresponding sentence as source
        assert prefixed_node.source_ids == [sentence_seg.id]


def test_step_with_attributes():
    """Pipeline with a step adding attributes to existing segments instead of returning new segments"""
    prefixer = _Prefixer(prefix="Hello! ")
    step_1 = PipelineStep(
        operation=prefixer, input_keys=["SENTENCE"], output_keys=["PREFIX"]
    )

    uppercaser = _Uppercaser()
    step_2 = PipelineStep(
        operation=uppercaser, input_keys=["PREFIX"], output_keys=["UPPERCASE"]
    )

    attribute_adder = _AttributeAdder(label="validated")
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
    sentence_segs = _get_sentence_segments()
    uppercased_segs = pipeline.process(sentence_segs)
    assert len(uppercased_segs) == len(sentence_segs)

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for uppercased_seg, sentence_seg in zip(uppercased_segs, sentence_segs):
        assert len(uppercased_seg.attrs) == 1
        attr = uppercased_seg.attrs[0]
        attr_node = graph.get_node(attr.id)
        # operation id is of outer pipeline operation
        assert attr_node.operation_id == pipeline.id
        # attribute node has corresponding sentence segment as source
        # (because it is what was given as input to the pipeline operation)
        assert attr_node.source_ids == [sentence_seg.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)

    for uppercased_seg in uppercased_segs:
        assert len(uppercased_seg.attrs) == 1
        attr = uppercased_seg.attrs[0]
        attr_node = sub_graph.get_node(attr.id)
        # operation id is of inner attribute adder operation
        assert attr_node.operation_id == attribute_adder.id
        # attribute node has corresponding uppercased segment as source
        assert attr_node.source_ids == [uppercased_seg.id]


def test_nested_pipeline():
    """Pipeline with a step that is also a pipeline"""
    # build inner pipeline
    uppercaser = _Uppercaser()
    sub_step_1 = PipelineStep(
        operation=uppercaser,
        input_keys=["SENTENCE"],
        output_keys=["UPPERCASE"],
    )

    prefix_1 = "Hi! "
    prefixer_1 = _Prefixer(prefix_1)
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
    prefixer_2 = _Prefixer(prefix_2)
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
    sentence_segs = _get_sentence_segments()
    output_segs = pipeline.process(sentence_segs)
    assert len(output_segs) == len(sentence_segs)

    # check outer main graph
    graph = prov_builder.graph
    graph.check_sanity()

    for output_seg, sentence_seg in zip(output_segs, sentence_segs):
        output_node = graph.get_node(output_seg.id)
        # operation id is of main pipeline operation
        assert output_node.operation_id == pipeline.id
        # uppercased node has corresponding sentence as source
        assert output_node.source_ids == [sentence_seg.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(pipeline.id)
    for output_seg, sentence_seg in zip(output_segs, sentence_segs):
        # node for result of sub pipeline
        node = sub_graph.get_node(output_seg.id)
        assert node.operation_id == sub_pipeline.id

        # node for result of prefixer before sub pipeline
        node = sub_graph.get_node(node.source_ids[0])
        assert node.operation_id == prefixer_2.id
        assert len(node.source_ids) == 1

        # stub node for input sentence segment
        node = sub_graph.get_node(node.source_ids[0])
        assert node.data_item_id == sentence_seg.id
        assert node.operation_id is None
        assert not node.source_ids

    # check innermost sub graph
    sub_graph = sub_graph.get_sub_graph(sub_pipeline.id)
    for output_seg, sentence_seg in zip(output_segs, sentence_segs):
        # node for result of prefixer inside sub pipeline
        node = sub_graph.get_node(output_seg.id)
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
