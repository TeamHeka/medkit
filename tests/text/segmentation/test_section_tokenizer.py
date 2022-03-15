import pytest

import medkit.text.segmentation.section_tokenizer as st
from medkit.core import Origin
from medkit.core.text import Span, Segment
from medkit.text.segmentation.section_tokenizer import (
    SectionTokenizer,
    SectionModificationRule,
)
import tests.data_utils as data_utils

TEST_CONFIG = [
    (
        "eds/clean/cas1",
        [
            ([Span(start=0, end=418)], "antecedent"),
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
    clean_text = Segment(
        origin=Origin(),
        label=st.DefaultConfig.input_label,
        spans=[Span(0, len(doc.text))],
        text=doc.text,
    )
    doc.add_annotation(clean_text)
    section_tokenizer.annotate_document(doc)
    section_ids = doc.segments.get(st.DefaultConfig.output_label)
    assert len(section_ids) == len(expected_sections)
    sections = [doc.get_annotation_by_id(section_id) for section_id in section_ids]
    for i, (spans, attr_value) in enumerate(expected_sections):
        assert sections[i].spans == spans
        assert sections[i].metadata["name"] == attr_value


def test_annotate_document_with_rules():
    filepath = TEST_CONFIG[0][0]
    doc = data_utils.get_text_document(filepath)
    clean_text = Segment(
        origin=Origin(),
        label=st.DefaultConfig.input_label,
        spans=[Span(0, len(doc.text))],
        text=doc.text,
    )
    doc.add_annotation(clean_text)
    section_dict = {"antecedent": ["Antécédents médicaux"], "examen": ["Examen :"]}
    section_rules = tuple(
        [
            SectionModificationRule(
                section_name="antecedent",
                new_section_name="antecedent_before_exam",
                order="BEFORE",
                other_sections=["examen"],
            ),
            SectionModificationRule(
                section_name="examen",
                new_section_name="exam_after_antecedent",
                order="AFTER",
                other_sections=["antecedent"],
            ),
        ]
    )
    section_tokenizer = SectionTokenizer(
        section_dict=section_dict, section_rules=section_rules
    )
    section_tokenizer.annotate_document(doc)
    section_ids = doc.segments.get(st.DefaultConfig.output_label)
    assert len(section_ids) == 2
    sections = [doc.get_annotation_by_id(section_id) for section_id in section_ids]
    sections_antecedent = [
        section
        for section in sections
        if section.metadata["name"] == "antecedent_before_exam"
    ]
    assert len(sections_antecedent) == 1
    section_examen = [
        section
        for section in sections
        if section.metadata["name"] == "exam_after_antecedent"
    ]
    assert len(section_examen) == 1
