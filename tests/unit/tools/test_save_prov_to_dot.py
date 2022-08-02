from medkit.core import (
    generate_id,
    ProvBuilder,
    OperationDescription,
    Attribute,
)
from medkit.core.text import Segment, Entity, Span
from medkit.tools.save_prov_to_dot import save_prov_to_dot


def _get_segment_and_entity(with_attr=False):
    sentence_segment = Segment(
        label="sentence", text="This is a sentence.", spans=[Span(0, 19)]
    )
    syntagma_segment = Segment(label="syntagma", text="a sentence", spans=[Span(8, 18)])
    entity = Entity(label="word", spans=[Span(10, 18)], text="sentence")
    if with_attr:
        attr = Attribute(label="negated", value=False)
        entity.add_attr(attr)

    return sentence_segment, syntagma_segment, entity


def _build_prov(prov_builder, sentence_segment, syntagma_segment, entity):
    tokenizer_desc = OperationDescription(name="SyntagmaTokenizer", id=generate_id())
    prov_builder.add_prov(
        syntagma_segment, tokenizer_desc, source_data_items=[sentence_segment]
    )

    matcher_desc = OperationDescription(name="EntityMatcher", id=generate_id())
    prov_builder.add_prov(entity, matcher_desc, source_data_items=[syntagma_segment])

    for attr in entity.get_attrs():
        # add attribute to entity
        neg_detector_desc = OperationDescription(
            name="NegationDetector", id=generate_id()
        )
        prov_builder.add_prov(
            attr, neg_detector_desc, source_data_items=[syntagma_segment]
        )


def test_basic(tmp_path):
    """Basic usage"""
    # build provenance
    sentence_segment, syntagma_segment, entity = _get_segment_and_entity()
    prov_builder = ProvBuilder()
    _build_prov(prov_builder, sentence_segment, syntagma_segment, entity)

    # export to dot
    path_to_dot = tmp_path / "prov.dot"
    with open(path_to_dot, mode="w") as file:
        save_prov_to_dot(
            prov_builder.graph,
            prov_builder.store,
            file,
            data_item_formatter=lambda a: f"{a.label}: {a.text}",
            op_formatter=lambda o: o.name,
        )
    dot_text = path_to_dot.read_text()

    # check dot entries
    assert (
        f'"{sentence_segment.id}" [label="sentence: This is a sentence."];\n'
        in dot_text
    )
    assert f'"{syntagma_segment.id}" [label="syntagma: a sentence"];\n' in dot_text
    assert f'"{entity.id}" [label="word: sentence"];\n' in dot_text
    assert (
        f'"{sentence_segment.id}" -> "{syntagma_segment.id}"'
        ' [label="SyntagmaTokenizer"];\n'
        in dot_text
    )
    assert (
        f'"{syntagma_segment.id}" -> "{entity.id}" [label="EntityMatcher"];\n'
        in dot_text
    )


def test_attrs(tmp_path):
    """Display attribute links"""
    # build provenance
    sentence_segment, syntagma_segment, entity = _get_segment_and_entity(with_attr=True)
    prov_builder = ProvBuilder()
    _build_prov(prov_builder, sentence_segment, syntagma_segment, entity)

    # export to dot
    path_to_dot = tmp_path / "prov.dot"
    with open(path_to_dot, mode="w") as file:
        save_prov_to_dot(
            prov_builder.graph,
            prov_builder.store,
            file,
            data_item_formatter=lambda a: f"{a.label}",
            op_formatter=lambda o: o.name,
        )
    dot_text = path_to_dot.read_text()

    # check attribute link in dot entries
    attr = entity.get_attrs()[0]
    assert (
        f'"{entity.id}" -> "{attr.id}" [style=dashed, color=grey,'
        ' label="attr", fontcolor=grey];\n'
        in dot_text
    )


def test_sub_prov_graph(tmp_path):
    """Handling of provenance sub graphs"""
    prov_builder = ProvBuilder()

    # build provenance for inner graph
    sentence_segment, syntagma_segment, entity = _get_segment_and_entity()
    sub_prov_builder = ProvBuilder(store=prov_builder.store)
    _build_prov(sub_prov_builder, sentence_segment, syntagma_segment, entity)

    # wrap it in outer pipeline graph
    pipeline_desc = OperationDescription(name="Pipeline", id=generate_id())
    prov_builder.add_prov_from_sub_graph([entity], pipeline_desc, sub_prov_builder)

    # render dot, not expanding sub graphs
    path_to_dot = tmp_path / "prov.dot"
    with open(path_to_dot, mode="w") as file:
        save_prov_to_dot(
            prov_builder.graph,
            prov_builder.store,
            file,
            data_item_formatter=lambda a: f"{a.label}: {a.text}",
            op_formatter=lambda o: o.name,
            max_sub_graph_depth=0,
        )
    dot_text = path_to_dot.read_text()

    # must have a dot entry for outer pipeline operation
    assert f'"{sentence_segment.id}" -> "{entity.id}" [label="Pipeline"];\n' in dot_text

    # render dot, expanding all sub graphs
    path_to_dot_full = tmp_path / "prov.dot"
    with open(path_to_dot_full, mode="w") as file:
        save_prov_to_dot(
            prov_builder.graph,
            prov_builder.store,
            file,
            data_item_formatter=lambda a: f"{a.label}: {a.text}",
            op_formatter=lambda o: o.name,
            max_sub_graph_depth=None,
        )
    dot_text_full = path_to_dot_full.read_text()

    # must have a dot entry for inner operations in sub graphs
    assert (
        f'"{sentence_segment.id}" -> "{syntagma_segment.id}"'
        ' [label="SyntagmaTokenizer"];\n'
        in dot_text_full
    )
    assert (
        f'"{syntagma_segment.id}" -> "{entity.id}" [label="EntityMatcher"];\n'
        in dot_text_full
    )
