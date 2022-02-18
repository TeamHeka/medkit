import pytest
import tests.data_utils as data_utils

from medkit.core.text import Span, TextBoundAnnotation
from medkit.text.segmentation.section_tokenizer import SectionTokenizer

TEST_CONFIG = [
    (
        "eds/clean/cas1",
        [
            ([Span(start=0, end=418)], "head"),
            ([Span(start=418, end=1231)], "mode_de_vie"),
            ([Span(start=1231, end=1606)], "conclusion"),
            ([Span(start=1606, end=1899)], "conclusion"),
            ([Span(start=1899, end=2268)], "conclusion"),
            ([Span(start=2268, end=3109)], "conclusion"),
            ([Span(start=3109, end=3246)], "antecedent"),
            ([Span(start=3246, end=3843)], "antecedent"),
            ([Span(start=3843, end=3916)], "antecedent"),
            ([Span(start=3916, end=6668)], "antecedent"),
            ([Span(start=6668, end=9094)], "conclusion"),
        ],
    ),
    ("eds/clean/cas2", [([Span(start=0, end=6671)], "head")]),
    (
        "eds/clean/cas3",
        [
            ([Span(start=0, end=315)], "head"),
            ([Span(start=315, end=369)], "examen_clinique"),
        ],
    ),
]


@pytest.mark.parametrize("filepath,expected_sections", TEST_CONFIG)
def test_annotate_document(filepath, expected_sections):
    doc = data_utils.get_text_document(filepath)
    section_tokenizer = SectionTokenizer.get_example()
    # section_tokenizer = SectionTokenizer(input_label="RAW_TEXT")
    raw_text = TextBoundAnnotation(
        ann_id="ann_id",
        origin_id="",
        label="CLEAN_TEXT",
        spans=[Span(0, len(doc.text))],
        text=doc.text,
    )
    doc.add_annotation(raw_text)
    assert doc.segments.get("CLEAN_TEXT") == ["ann_id"]
    section_tokenizer.annotate_document(doc)
    section_ids = doc.segments.get("SECTION")
    assert len(section_ids) != 0
    sections = [doc.get_annotation_by_id(section_id) for section_id in section_ids]
    attributes = [doc.get_attributes_by_annotation(section.id) for section in sections]
    for i, (spans, attr_value) in enumerate(expected_sections):
        assert sections[i].spans == spans
        assert attributes[i].get("SECTION").value == attr_value
