from medkit.io.brat import BratConverter


def test_load():
    brat_converter = BratConverter()
    assert brat_converter.name == "BratConverter"
    assert brat_converter.format == "brat"
    collection = brat_converter.load(
        dir_path="tests/data/brat/BratConverter", text_extension=".txt"
    )
    assert len(collection.documents) == 1
    doc = collection.documents[0]
    assert doc.text.startswith("The")
    assert "disease" in doc.entities.keys()
    T4 = doc.entities["disease"][1]
    assert doc.get_annotation_by_id(T4).text == "Hypothyroidism"
    assert T4 in doc.attributes.keys()
