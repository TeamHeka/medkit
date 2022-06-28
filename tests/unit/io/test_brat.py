from medkit.core import ProvBuilder
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
    assert len(doc.entities.get("medication", [])) == 2
    assert len(doc.entities.get("disease", [])) == 2
    assert len(doc.entities.get("vitamin", [])) == 3
    # relations are now handled by TextDocument
    assert len(doc.get_relations()) == 2

    # check relation for T1
    entity_id_t1 = doc.entities["medication"][0]
    entity_id_t3 = doc.entities["disease"][0]
    relations_ent_t1 = doc.get_relations_by_source_id(entity_id_t1)
    assert len(relations_ent_t1) == 1

    assert relations_ent_t1[0].label == "treats"
    assert relations_ent_t1[0].target_id == entity_id_t3
    assert entity_id_t3 not in doc.relations_by_source

    # check entity T4 disease
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


def test_relations():
    brat_converter = BratInputConverter()
    doc: TextDocument = brat_converter.load(dir_path="tests/data/brat/").documents[0]
    relations = doc.get_relations()
    assert len(relations) == 2

    assert relations[0].source_id == doc.entities["medication"][0]
    assert relations[0].target_id == doc.entities["disease"][0]
    assert relations[0].label == "treats"

    assert relations[1].source_id == doc.entities["medication"][1]
    assert relations[1].target_id == doc.entities["disease"][1]
    assert relations[1].label == "treats"


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
