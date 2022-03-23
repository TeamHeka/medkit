from medkit.core import generate_id, OperationDescription
from medkit.core.prov_builder import ProvBuilder

from tests.core.prov_builder._common import get_text_items, Prefixer, Splitter, Merger


class _PrefixerWrapper:
    def __init__(self, prov_builder):
        self.id = generate_id()
        self.prefixer = Prefixer()
        self.prov_builder = prov_builder
        self.sub_prov_builder = ProvBuilder(prov_builder.store)
        self.prefixer.prov_builder = self.sub_prov_builder
        self.description = OperationDescription(id=self.id, name="PrefixerWrapper")

    def process(self, input_items):
        output_items = self.prefixer.prefix(input_items)

        self.prov_builder.add_prov_from_sub_graph(
            output_items, self.description, self.sub_prov_builder
        )

        return output_items


def test_single_operation():
    """Wrapper operation wrapping only one operation"""
    builder = ProvBuilder()
    wrapper = _PrefixerWrapper(builder)
    input_items = get_text_items(2)
    output_items = wrapper.process(input_items)

    # check outer main graph
    graph = builder.graph
    graph.check_sanity()
    # main graph must have a node for each input item and each output item
    assert len(graph.get_nodes()) == len(input_items) + len(output_items)

    for input_item, output_item in zip(input_items, output_items):
        input_node = graph.get_node(input_item.id)
        assert input_node.data_item_id == input_item.id
        assert input_node.operation_id is None
        assert not input_node.source_ids
        # input node has corresponding output item as derived
        assert input_node.derived_ids == [output_item.id]

        output_node = graph.get_node(output_item.id)
        assert output_node.data_item_id == output_item.id
        # operation id is of outer wrapper operation
        assert output_node.operation_id == wrapper.id
        # output node has corresponding input item as source
        assert output_node.source_ids == [input_item.id]
        assert not output_node.derived_ids

    # check inner sub graph
    assert graph.has_sub_graph(wrapper.id)
    sub_graph = graph.get_sub_graph(wrapper.id)
    # sub graph must have a node for each input item and each output item
    assert len(sub_graph.get_nodes()) == len(input_items) + len(output_items)

    for input_item, output_item in zip(input_items, output_items):
        input_node = sub_graph.get_node(input_item.id)
        assert input_node.data_item_id == input_item.id
        assert input_node.operation_id is None
        assert not input_node.source_ids
        # input node has corresponding output item as derived
        assert input_node.derived_ids == [output_item.id]

        output_node = sub_graph.get_node(output_item.id)
        assert output_node.data_item_id == output_item.id
        # operation id is of inner prefixer
        assert output_node.operation_id == wrapper.prefixer.id
        # output node has corresponding input item as source
        assert output_node.source_ids == [input_item.id]
        assert not output_node.derived_ids


class _DoublePrefixerWrapper:
    def __init__(self, prov_builder):
        self.id = generate_id()
        self.prefixer_1 = Prefixer()
        self.prefixer_2 = Prefixer()
        self.prov_builder = prov_builder
        self.sub_prov_builder = ProvBuilder(prov_builder.store)
        self.prefixer_1.prov_builder = self.sub_prov_builder
        self.prefixer_2.prov_builder = self.sub_prov_builder
        self.description = OperationDescription(
            id=self.id, name="DoublePrefixerWrapper"
        )

    def process(self, input_items):
        intermediate_items = self.prefixer_1.prefix(input_items)
        output_items = self.prefixer_2.prefix(intermediate_items)

        self.prov_builder.add_prov_from_sub_graph(
            output_items, self.description, self.sub_prov_builder
        )

        return output_items


def test_intermediate_operation():
    """Wrapper operation wrapping 2 consecutive operations,
    only the output of the 2d operation is returned"""
    builder = ProvBuilder()
    wrapper = _DoublePrefixerWrapper(builder)
    input_items = get_text_items(2)
    output_items = wrapper.process(input_items)

    # check outer main graph
    graph = builder.graph
    graph.check_sanity()
    # graph must have a node for each input item and each output item
    assert len(graph.get_nodes()) == len(input_items) + len(output_items)

    for input_item, output_item in zip(input_items, output_items):
        input_node = graph.get_node(input_item.id)
        # input node has corresponding output item as derived
        assert input_node.derived_ids == [output_item.id]

        output_node = graph.get_node(output_item.id)
        # operation id is of outer wrapper operation
        assert output_node.operation_id == wrapper.id
        # output node has corresponding input item as source
        assert output_node.source_ids == [input_item.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(wrapper.id)
    # sub graph must have a node for each input item, each intermediate item and each output item
    assert len(sub_graph.get_nodes()) == len(input_items) + 2 * len(output_items)

    for input_item, output_item in zip(input_items, output_items):
        assert sub_graph.has_node(input_item.id)

        output_node = sub_graph.get_node(output_item.id)
        # operation id is of inner 1st prefixer
        assert output_node.operation_id == wrapper.prefixer_2.id
        # output node has 1 intermediate item as source
        assert len(output_node.source_ids) == 1
        intermediate_item_id = output_node.source_ids[0]

        intermediate_node = sub_graph.get_node(intermediate_item_id)
        # operation id is of inner 2d prefixer
        assert intermediate_node.operation_id == wrapper.prefixer_1.id
        # intermediate node has corresponding input item as source
        assert intermediate_node.source_ids == [input_item.id]
        # intermediate node has corresponding output item as derived
        assert intermediate_node.derived_ids == [output_item.id]

        input_node = sub_graph.get_node(input_item.id)
        # input node has corresponding intermediate item as derived
        assert input_node.derived_ids == [intermediate_item_id]


class _PrefixerMergerWrapper:
    def __init__(self, prov_builder):
        self.id = generate_id()
        self.prefixer = Prefixer()
        self.merger = Merger()
        self.prov_builder = prov_builder
        self.sub_prov_builder = ProvBuilder(prov_builder.store)
        self.prefixer.prov_builder = self.sub_prov_builder
        self.merger.prov_builder = self.sub_prov_builder
        self.description = OperationDescription(
            id=self.id, name="PrefixerMergerWrapper"
        )

    def process(self, input_items):
        intermediate_items = self.prefixer.prefix(input_items)
        output_item = self.merger.merge(intermediate_items)

        self.prov_builder.add_prov_from_sub_graph(
            [output_item], self.description, self.sub_prov_builder
        )

        return output_item


def test_multi_input_operation():
    """Wrapper operation wrapping an operation deriving one item from multiple input (merger)"""
    builder = ProvBuilder()
    wrapper = _PrefixerMergerWrapper(builder)
    input_items = get_text_items(2)
    output_item = wrapper.process(input_items)

    # check outer main graph
    graph = builder.graph
    graph.check_sanity()
    # graph must have a node for each input item and each output item
    assert len(graph.get_nodes()) == len(input_items) + 1

    output_node = graph.get_node(output_item.id)
    # operation id is of outer wrapper operation
    assert output_node.operation_id == wrapper.id
    # output item has all input items as sources
    assert output_node.source_ids == [i.id for i in input_items]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(wrapper.id)
    # sub graph must have a node for each input item, each prefixed item and each output item
    nb_prefixed_items = len(input_items)
    assert len(sub_graph.get_nodes()) == len(input_items) + nb_prefixed_items + 1
    # merged item has all prefixed items as sources
    merged_node = sub_graph.get_node(output_item.id)
    assert merged_node.operation_id == wrapper.merger.id
    assert len(merged_node.source_ids) == nb_prefixed_items

    for prefixed_item_id, input_item in zip(merged_node.source_ids, input_items):
        prefixed_node = sub_graph.get_node(prefixed_item_id)
        # operation id is of inner prefixer
        assert prefixed_node.operation_id == wrapper.prefixer.id
        # prefixed_item node has corresponding input item as source
        assert prefixed_node.source_ids == [input_item.id]


class _SplitterPrefixerWrapper:
    def __init__(self, prov_builder):
        self.id = generate_id()
        self.splitter = Splitter()
        self.prefixer = Prefixer()
        self.prov_builder = prov_builder
        self.sub_prov_builder = ProvBuilder(prov_builder.store)
        self.splitter.prov_builder = self.sub_prov_builder
        self.prefixer.prov_builder = self.sub_prov_builder
        self.description = OperationDescription(
            id=self.id, name="SplitterPrefixerMWrapper"
        )

    def process(self, input_items):
        intermediate_items = self.splitter.split(input_items)
        output_items = self.prefixer.prefix(intermediate_items)

        self.prov_builder.add_prov_from_sub_graph(
            output_items, self.description, self.sub_prov_builder
        )

        return output_items


def test_multi_output_operation():
    """Wrapper operation wrapping an operation derived several items from single input item (splitter)"""
    builder = ProvBuilder()
    wrapper = _SplitterPrefixerWrapper(builder)
    input_items = get_text_items(2)
    output_items = wrapper.process(input_items)

    # check outer main graph
    graph = builder.graph
    graph.check_sanity()
    # graph must have a node for each input item and each output item
    assert len(graph.get_nodes()) == len(input_items) + len(output_items)

    for i, output_item in enumerate(output_items):
        input_item = input_items[i // 2]
        # output item has corresponding input item as source
        output_node = graph.get_node(output_item.id)
        # operation id is of outer wrapper operation
        assert output_node.operation_id == wrapper.id
        assert output_node.source_ids == [input_item.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(wrapper.id)
    # sub graph must have a node for each input item, each prefixed item and each output item
    nb_split_items = 2 * len(input_items)
    assert len(sub_graph.get_nodes()) == len(input_items) + nb_split_items + len(
        output_items
    )

    for i, prefixed_item in enumerate(output_items):
        input_item = input_items[i // 2]

        prefixed_node = sub_graph.get_node(prefixed_item.id)
        assert prefixed_node.operation_id == wrapper.prefixer.id
        # prefixed node has one split item as source
        assert len(prefixed_node.source_ids) == 1

        split_item_id = prefixed_node.source_ids[0]
        split_node = sub_graph.get_node(split_item_id)
        # operation id is of inner splitter
        assert split_node.operation_id == wrapper.splitter.id
        # split node has its corresponding input item as source
        assert split_node.source_ids == [input_item.id]


class _BranchedPrefixerWrapper:
    def __init__(self, prov_builder):
        self.id = generate_id()
        self.prefixer_1 = Prefixer()
        self.prefixer_2 = Prefixer()
        self.prov_builder = prov_builder
        self.sub_prov_builder = ProvBuilder(prov_builder.store)
        self.prefixer_1.prov_builder = self.sub_prov_builder
        self.prefixer_2.prov_builder = self.sub_prov_builder
        self.description = OperationDescription(
            id=self.id, name="BrancherPrefixerWrapper"
        )

    def process(self, input_items):
        prefixed_items = self.prefixer_1.prefix(input_items)
        double_prefixed_items = self.prefixer_2.prefix(prefixed_items)

        output_items = prefixed_items + double_prefixed_items
        self.prov_builder.add_prov_from_sub_graph(
            output_items, self.description, self.sub_prov_builder
        )

        return prefixed_items, double_prefixed_items


def test_operation_reusing_output():
    """Wrapper operation  wrapping 2 operations, with 2 outputs,
    the 2d output being the result of the 2d operation applied on the 1st output
    (make sure we don't try to add the same node twice in the main group)"""
    builder = ProvBuilder()
    wrapper = _BranchedPrefixerWrapper(builder)
    input_items = get_text_items(2)
    prefixed_items, double_prefixed_items = wrapper.process(input_items)

    # check outer main graph
    graph = builder.graph
    graph.check_sanity()
    # graph must have a node for each input item and each output prefixed_items
    assert len(graph.get_nodes()) == len(input_items) + len(prefixed_items) + len(
        double_prefixed_items
    )

    for (input_item, prefixed_item) in zip(input_items, prefixed_items):
        prefixed_node = graph.get_node(prefixed_item.id)
        # operation id is of outer wrapper operation
        assert prefixed_node.operation_id == wrapper.id
        # prefixed node has corresponding input item as source
        assert prefixed_node.source_ids == [input_item.id]
    for (input_item, double_prefixed_item) in zip(input_items, prefixed_items):
        double_prefixed_node = graph.get_node(double_prefixed_item.id)
        # operation id is of outer wrapper operation
        assert double_prefixed_node.operation_id == wrapper.id
        # prefixed node has corresponding input item as source
        assert double_prefixed_node.source_ids == [input_item.id]

    # check inner sub graph
    sub_graph = graph.get_sub_graph(wrapper.id)
    # sub graph must have a node for each input item, each prefixed item and each double prefixed item
    assert len(sub_graph.get_nodes()) == len(input_items) + len(prefixed_items) + len(
        double_prefixed_items
    )

    for (input_item, prefixed_item) in zip(input_items, prefixed_items):
        prefixed_node = sub_graph.get_node(prefixed_item.id)
        # operation id is of inner 1st prefixer
        assert prefixed_node.operation_id == wrapper.prefixer_1.id
        # prefixed node has corresponding input item as source
        assert prefixed_node.source_ids == [input_item.id]

    for (prefixed_item, double_prefixed_item) in zip(
        prefixed_items, double_prefixed_items
    ):
        double_prefixed_node = sub_graph.get_node(double_prefixed_item.id)
        # operation id is of inner 2d prefixer
        assert double_prefixed_node.operation_id == wrapper.prefixer_2.id
        # double prefixed node has corresponding prefixed item as source
        assert double_prefixed_node.source_ids == [prefixed_item.id]


def test_consecutive_calls():
    """Make sure add_prov_from_sub_graph can be called several times"""
    builder = ProvBuilder()
    wrapper = _DoublePrefixerWrapper(builder)
    input_items_1 = get_text_items(2)
    output_items_1 = wrapper.process(input_items_1)
    input_items_2 = get_text_items(2)
    output_items_2 = wrapper.process(input_items_2)
    input_items = input_items_1 + input_items_2
    output_items = output_items_1 + output_items_2

    # check outer main graph
    graph = builder.graph
    graph.check_sanity()
    # graph must have a node for each input item and each output item
    assert len(graph.get_nodes()) == len(input_items) + len(output_items)

    # check inner sub graph
    sub_graph = graph.get_sub_graph(wrapper.id)
    # sub graph must have a node for each input item, each intermediate item and each output item
    assert len(sub_graph.get_nodes()) == len(input_items) + 2 * len(output_items)
