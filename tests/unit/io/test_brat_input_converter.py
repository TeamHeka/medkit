from medkit.core import ProvTracer
from medkit.core.text import Span
from medkit.io.brat import BratInputConverter


def test_load():
    brat_converter = BratInputConverter()
    assert brat_converter.description.name == "BratInputConverter"
    docs = brat_converter.load(dir_path="tests/data/brat/")
    # 2d .ann file in dir ignored because it has no corresponding .txt
    assert len(docs) == 1

    doc = docs[0]

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
    relations_ent_t1 = doc.get_relations_by_source_id(entity_t1.uid)
    assert len(relations_ent_t1) == 1

    assert relations_ent_t1[0].label == "treats"
    assert relations_ent_t1[0].target_id == entity_t3.uid
    assert not doc.get_relations_by_source_id(entity_t3.uid)

    # check entity T4 disease
    entity_1 = doc.get_annotations_by_label("disease")[1]
    assert entity_1.label == "disease"
    assert entity_1.text == "Hypothyroidism"
    assert entity_1.spans == [Span(147, 161)]
    assert entity_1.metadata.get("brat_id") == "T4"

    # check attribute
    assert len(entity_1.attrs) == 1
    attr = entity_1.attrs.get()[0]
    assert attr.label == "antecedent"
    assert attr.value is None
    assert attr.metadata.get("brat_id") == "A3"

    # check multi-span entity
    entity_2 = doc.get_annotations_by_label("vitamin")[1]
    assert entity_2.spans == [Span(251, 260), Span(263, 264)]


def test_relations():
    brat_converter = BratInputConverter()
    doc = brat_converter.load(dir_path="tests/data/brat/")[0]
    relations = doc.get_relations()
    assert len(relations) == 2

    assert relations[0].source_id == doc.get_annotations_by_label("medication")[0].uid
    assert relations[0].target_id == doc.get_annotations_by_label("disease")[0].uid
    assert relations[0].label == "treats"

    assert relations[1].source_id == doc.get_annotations_by_label("medication")[1].uid
    assert relations[1].target_id == doc.get_annotations_by_label("disease")[1].uid
    assert relations[1].label == "treats"


def test_load_no_anns():
    brat_converter = BratInputConverter()
    docs = brat_converter.load(dir_path="tests/data/text")
    for doc in docs:
        assert len(doc.get_annotations()) == 0


def test_prov():
    brat_converter = BratInputConverter()
    prov_tracer = ProvTracer()
    brat_converter.set_prov_tracer(prov_tracer)
    docs = brat_converter.load(dir_path="tests/data/brat")

    doc = docs[0]
    entity = doc.get_annotations_by_label("disease")[1]
    prov = prov_tracer.get_prov(entity.uid)
    assert prov.data_item == entity
    assert prov.op_desc == brat_converter.description
    assert len(prov.source_data_items) == 0
