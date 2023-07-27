from medkit.core.text import Entity, Span
from medkit.core.text.span import ModifiedSpan
from medkit.text.postprocessing import filter_overlapping_entities


def test_filter_entities():
    entities = [
        Entity(label="CHEM", spans=[Span(0, 12)], text="chlorhydrate"),
        Entity(label="CHEM", spans=[Span(0, 24)], text="chlorhydrate de fentanyl"),
        Entity(label="CHEM", spans=[Span(16, 24)], text="fentanyl"),
    ]

    filtered_entities = filter_overlapping_entities(entities)

    # check only the longest is returned
    assert len(filtered_entities) == 1
    assert filtered_entities[0].uid == entities[1].uid


def test_filter_entities_with_modified_span():
    # test using 'chlorhydrate\n\nde\n\nfentanyl' as raw text
    entities = [
        Entity(label="CHEM", spans=[Span(0, 12)], text="chlorhydrate"),
        Entity(
            label="CHEM",
            spans=[
                Span(start=0, end=12),
                ModifiedSpan(length=1, replaced_spans=[Span(start=12, end=14)]),
                Span(start=14, end=16),
                ModifiedSpan(length=1, replaced_spans=[Span(start=16, end=18)]),
                Span(start=18, end=26),
            ],
            text="chlorhydrate de fentanyl",
        ),
        Entity(label="CHEM", spans=[Span(18, 26)], text="fentanyl"),
    ]
    filtered_entities = filter_overlapping_entities(entities)

    # check only the longest is returned
    assert len(filtered_entities) == 1
    assert filtered_entities[0].uid == entities[1].uid
