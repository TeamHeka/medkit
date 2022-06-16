from medkit.core import ProvBuilder
from medkit.core.text import Span
from medkit.io.brat import BratInputConverter


def test_load():
    brat_converter = BratInputConverter()
    assert brat_converter.description.name == "BratInputConverter"
    collection = brat_converter.load(dir_path="tests/data/brat/")
    assert len(collection.documents) == 2

    doc = collection.documents[0]

    assert "path_to_text" in doc.metadata
    assert "path_to_ann" in doc.metadata

    path_to_text = doc.metadata["path_to_text"]
    with open(path_to_text) as file:
        text = file.read()
    assert doc.text == text

    # all expected annotations should be present
    anns = doc.get_annotations()
    assert len(anns) == 9
    assert len(doc.entities.get("medication", [])) == 2
    assert len(doc.entities.get("disease", [])) == 2
    assert len(doc.entities.get("vitamin", [])) == 3
    # FIXME relations are not handled by TextDocument for now
    assert len(doc.relations.get("treats", [])) == 0

    # check entity
    entity_id_1 = doc.entities["disease"][1]
    entity_1 = doc.get_annotation_by_id(entity_id_1)
    assert entity_1.label == "disease"
    assert entity_1.text == "Hypothyroidism"
    assert entity_1.spans == [Span(147, 161)]
    assert entity_1.metadata.get("brat_id") == "T4"

    # check attribute
    assert len(entity_1.attrs) == 1
    attr = entity_1.attrs[0]
    assert attr.label == "antecedent"
    assert attr.value is None
    assert attr.metadata.get("brat_id") == "A3"

    # check multi-span entity
    entity_id_2 = doc.entities["vitamin"][1]
    entity_2 = doc.get_annotation_by_id(entity_id_2)
    assert entity_2.spans == [Span(251, 260), Span(263, 264)]

    # TODO relations


def test_load_no_anns():
    brat_converter = BratInputConverter()
    collection = brat_converter.load(dir_path="tests/data/text")
    for doc in collection.documents:
        assert doc.text is not None
        assert len(doc.get_annotations()) == 0


def test_prov():
    brat_converter = BratInputConverter()
    prov_builder = ProvBuilder()
    brat_converter.set_prov_builder(prov_builder)
    collection = brat_converter.load(dir_path="tests/data/brat")
    graph = prov_builder.graph

    doc = collection.documents[0]
    entity_id = doc.entities["disease"][1]
    node = graph.get_node(entity_id)
    assert node.data_item_id == entity_id
    assert node.operation_id == brat_converter.id
    assert not node.source_ids
