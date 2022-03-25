from medkit.core import generate_id, ProvGraph, ProvNode, OperationDescription
from medkit.core.text import TextDocument, Segment, Entity, Span
from medkit.tools.save_prov_to_dot import save_prov_to_dot


def _get_segment_and_entity():
    sentence_segment = Segment(
        label="sentence", text="This is a sentence.", spans=[Span(0, 19)]
    )
    syntagma_segment = Segment(label="syntagma", text="a sentence", spans=[Span(8, 18)])
    entity = Entity(label="word", spans=[Span(10, 18)], text="sentence")
    return sentence_segment, syntagma_segment, entity


def _get_doc_and_prov_graph(sentence_segment, syntagma_segment, entity):
    # build document
    doc = TextDocument()

    doc.add_annotation(sentence_segment)

    tokenizer_desc = OperationDescription(name="SyntagmaTokenizer", id=generate_id())
    doc.add_operation(tokenizer_desc)
    doc.add_annotation(syntagma_segment)

    matcher_desc = OperationDescription(name="EntityMatcher", id=generate_id())
    doc.add_operation(matcher_desc)
    doc.add_annotation(entity)

    # build prov graph
    prov_graph = ProvGraph()

    sentence_node = ProvNode(
        sentence_segment.id, None, source_ids=[], derived_ids=[entity.id]
    )
    prov_graph.add_node(sentence_node)

    syntagma_node = ProvNode(
        syntagma_segment.id,
        tokenizer_desc.id,
        source_ids=[sentence_segment.id],
        derived_ids=[],
    )
    prov_graph.add_node(syntagma_node)

    entity_node = ProvNode(
        entity.id, matcher_desc.id, source_ids=[syntagma_segment.id], derived_ids=[]
    )
    prov_graph.add_node(entity_node)

    return doc, prov_graph


def test_basic(tmp_path):
    text_segment, syntagma_segment, entity = _get_segment_and_entity()
    doc, prov_graph = _get_doc_and_prov_graph(text_segment, syntagma_segment, entity)

    path_to_dot = tmp_path / "prov.dot"
    with open(path_to_dot, mode="w") as file:
        save_prov_to_dot(
            prov_graph,
            doc,
            file,
            ann_formatter=lambda a: f"{a.label}: {a.text}",
            op_formatter=lambda o: o.name,
        )
    with open(path_to_dot) as file:
        dot_lines = file.readlines()

    assert (
        f'"{text_segment.id}" [label="sentence: This is a sentence."];\n' in dot_lines
    )
    assert f'"{syntagma_segment.id}" [label="syntagma: a sentence"];\n' in dot_lines
    assert f'"{entity.id}" [label="word: sentence"];\n' in dot_lines
    assert (
        f'"{text_segment.id}" -> "{syntagma_segment.id}" [label="SyntagmaTokenizer"];\n'
        in dot_lines
    )
    assert (
        f'"{syntagma_segment.id}" -> "{entity.id}" [label="EntityMatcher"];\n'
        in dot_lines
    )


def test_sub_prov_graph(tmp_path):
    text_segment, syntagma_segment, entity = _get_segment_and_entity()
    doc, sub_prov_graph = _get_doc_and_prov_graph(
        text_segment, syntagma_segment, entity
    )

    pipeline_desc = OperationDescription(name="Pipeline", id=generate_id())
    doc.add_operation(pipeline_desc)

    main_prov_graph = ProvGraph()
    node = ProvNode(entity.id, pipeline_desc.id, source_ids=[text_segment.id])
    main_prov_graph.add_node(node)
    main_prov_graph.add_sub_graph(pipeline_desc.id, sub_prov_graph)

    path_to_dot = tmp_path / "prov.dot"
    with open(path_to_dot, mode="w") as file:
        save_prov_to_dot(
            main_prov_graph,
            doc,
            file,
            ann_formatter=lambda a: f"{a.label}: {a.text}",
            op_formatter=lambda o: o.name,
            max_sub_graph_depth=0,
        )
    with open(path_to_dot) as file:
        dot_lines = file.readlines()

    assert f'"{text_segment.id}" -> "{entity.id}" [label="Pipeline"];\n' in dot_lines

    path_to_dot_full = tmp_path / "prov.dot"
    with open(path_to_dot_full, mode="w") as file:
        save_prov_to_dot(
            main_prov_graph,
            doc,
            file,
            ann_formatter=lambda a: f"{a.label}: {a.text}",
            op_formatter=lambda o: o.name,
            max_sub_graph_depth=None,
        )
    with open(path_to_dot_full) as file:
        dot_full_lines = file.readlines()

    assert (
        f'"{text_segment.id}" -> "{syntagma_segment.id}" [label="SyntagmaTokenizer"];\n'
        in dot_full_lines
    )
    assert (
        f'"{syntagma_segment.id}" -> "{entity.id}" [label="EntityMatcher"];\n'
        in dot_full_lines
    )
