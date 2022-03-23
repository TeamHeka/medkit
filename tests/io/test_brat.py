from medkit.io.brat import BratInputConverter


def test_load():
    brat_converter = BratInputConverter()
    assert brat_converter.description.name == "BratInputConverter"
    collection = brat_converter.load(dir_path="tests/data/brat/BratConverter")
    assert len(collection.documents) == 1
    doc = collection.documents[0]
    assert brat_converter.description.id in doc.operations.keys()
    assert doc.text.startswith("The")
    assert "disease" in doc.entities.keys()
    T4 = doc.entities["disease"][1]
    entity = doc.get_annotation_by_id(T4)
    assert entity.text == "Hypothyroidism"
    assert len(entity.attrs) == 1
    assert entity.attrs[0].label == "antecedent"
