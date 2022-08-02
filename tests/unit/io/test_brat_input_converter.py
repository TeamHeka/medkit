from medkit.core import ProvTracer
from medkit.core.text import Span
from medkit.core.text.document import TextDocument
from medkit.io.brat import BratInputConverter


def test_load():
    brat_converter = BratInputConverter()
    assert brat_converter.description.name == "BratInputConverter"
    collection = brat_converter.load(dir_path="tests/data/brat/")
    assert len(collection.documents) == 2

    doc: TextDocument = collection.documents[0]

    assert "path_to_text" in doc.metadata
    assert "path_to_ann" in doc.metadata

    path_to_text = doc.metadata["path_to_text"]
    with open(path_to_text) as file:
        text = file.read()
    assert doc.text == text

    # all expected annotations should be present
    anns = doc.get_annotations()
    assert len(anns) == 9
    assert len(doc.get_annotations_by_label("medication")) == 2
    assert len(doc.get_annotations_by_label("disease")) == 2
    assert len(doc.get_annotations_by_label("vitamin")) == 3
    # relations are now handled by TextDocument
    assert len(doc.get_relations()) == 2

    # check relation for T1
    entity_t1 = doc.get_annotations_by_label("medication")[0]
    entity_t3 = doc.get_annotations_by_label("disease")[0]
    relations_ent_t1 = doc.get_relations_by_source_id(entity_t1.id)
    assert len(relations_ent_t1) == 1

    assert relations_ent_t1[0].label == "treats"
    assert relations_ent_t1[0].target_id == entity_t3.id
    assert not doc.get_relations_by_source_id(entity_t3.id)

    # check entity T4 disease
    entity_1 = doc.get_annotations_by_label("disease")[1]
    assert entity_1.label == "disease"
    assert entity_1.text == "Hypothyroidism"
    assert entity_1.spans == [Span(147, 161)]
    assert entity_1.metadata.get("brat_id") == "T4"

    # check attribute
    attrs = entity_1.get_attrs()
    assert len(attrs) == 1
    attr = attrs[0]
    assert attr.label == "antecedent"
    assert attr.value is None
    assert attr.metadata.get("brat_id") == "A3"

    # check multi-span entity
    entity_2 = doc.get_annotations_by_label("vitamin")[1]
    assert entity_2.spans == [Span(251, 260), Span(263, 264)]


def test_relations():
    brat_converter = BratInputConverter()
    doc: TextDocument = brat_converter.load(dir_path="tests/data/brat/").documents[0]
    relations = doc.get_relations()
    assert len(relations) == 2

    assert relations[0].source_id == doc.get_annotations_by_label("medication")[0].id
    assert relations[0].target_id == doc.get_annotations_by_label("disease")[0].id
    assert relations[0].label == "treats"

    assert relations[1].source_id == doc.get_annotations_by_label("medication")[1].id
    assert relations[1].target_id == doc.get_annotations_by_label("disease")[1].id
    assert relations[1].label == "treats"


def test_load_no_anns():
    brat_converter = BratInputConverter()
    collection = brat_converter.load(dir_path="tests/data/text")
    for doc in collection.documents:
        assert doc.text is not None
        assert len(doc.get_annotations()) == 0


def test_prov():
    brat_converter = BratInputConverter()
    prov_tracer = ProvTracer()
    brat_converter.set_prov_tracer(prov_tracer)
    collection = brat_converter.load(dir_path="tests/data/brat")
    graph = prov_tracer.graph

    doc = collection.documents[0]
    entity = doc.get_annotations_by_label("disease")[1]
    node = graph.get_node(entity.id)
    assert node.data_item_id == entity.id
    assert node.operation_id == brat_converter.id
    assert not node.source_ids
