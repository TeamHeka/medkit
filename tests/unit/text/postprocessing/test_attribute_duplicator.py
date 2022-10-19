from medkit.core import Attribute, ProvTracer
from medkit.core.text import Segment, TextDocument
from medkit.core.text import span_utils
from medkit.text.postprocessing import AttributeDuplicator


def _extract_segment(segment, ranges, label):
    text, spans = span_utils.extract(segment.text, segment.spans, ranges)
    return Segment(label=label, spans=spans, text=text)


def _get_doc():
    text = (
        """Sa mère présente douleurs abdominales mais le patient n'a pas une maladie."""
    )
    doc = TextDocument(text)
    sentence = _extract_segment(doc.raw_segment, [(0, 73)], "sentence")
    syntagme_0 = _extract_segment(sentence, [(0, 37)], "syntagme")
    syntagme_1 = _extract_segment(sentence, [(37, 73)], "syntagme")
    # add is_family in sentence
    sentence.add_attr(Attribute(label="is_family", value=True))
    sentence.add_attr(Attribute(label="family_trigger", value="Mother"))

    # add is_negated in syntagmes
    syntagme_0.add_attr(Attribute(label="is_negated", value=False))
    syntagme_1.add_attr(Attribute(label="is_negated", value=True))

    # create entities (target)
    target_0 = _extract_segment(doc.raw_segment, [(17, 37)], "disease")
    target_1 = _extract_segment(doc.raw_segment, [(66, 73)], "disease")

    for ann in [sentence, syntagme_0, syntagme_1, target_0, target_1]:
        doc.add_annotation(ann)
    return doc


def test_default_attribute_duplicator():
    doc = _get_doc()
    sentences = doc.get_annotations_by_label("sentence")
    syntagmes = doc.get_annotations_by_label("syntagme")
    targets = doc.get_annotations_by_label("disease")

    # check no attrs in targets
    assert all(not target.get_attrs() for target in targets)

    # define attr duplicators
    propagator_1 = AttributeDuplicator(attr_labels=["is_family"])
    propagator_2 = AttributeDuplicator(attr_labels=["is_negated"])

    # is_family was 'detected' in sentences
    propagator_1.run(sentences, targets)
    # is_negated was 'detected' in syntagmes
    propagator_2.run(syntagmes, targets)

    # check new attrs
    assert all(len(target.get_attrs()) == 2 for target in targets)

    # check first target
    target = targets[0]
    negated = target.get_attrs_by_label("is_negated")[0]
    family = target.get_attrs_by_label("is_family")[0]
    assert len(target.get_attrs_by_label("family_trigger")) == 0
    assert not negated.value
    assert family.value

    # check second target
    target = targets[1]
    negated = target.get_attrs_by_label("is_negated")[0]
    family = target.get_attrs_by_label("is_family")[0]
    assert len(target.get_attrs_by_label("family_trigger")) == 0
    assert negated.value
    assert family.value


def test_duplicate_several_attrs():
    doc = _get_doc()
    sentences = doc.get_annotations_by_label("sentence")
    targets = doc.get_annotations_by_label("disease")

    # check no attrs in targets
    assert all(not target.get_attrs() for target in targets)

    # define attr duplicator
    propagator = AttributeDuplicator(attr_labels=["is_family", "family_trigger"])
    # attrs were 'detected' in sentences
    propagator.run(sentences, targets)

    # check new attrs
    attr_src_family = sentences[0].get_attrs_by_label("is_family")[0]
    attr_src_family_trigger = sentences[0].get_attrs_by_label("family_trigger")[0]

    assert all(len(target.get_attrs()) == 2 for target in targets)
    for target in targets:
        assert len(target.get_attrs_by_label("is_negated")) == 0
        family = target.get_attrs_by_label("is_family")[0]
        family_trigger = target.get_attrs_by_label("family_trigger")[0]
        assert family.value == attr_src_family.value
        assert family_trigger.value == attr_src_family_trigger.value == "Mother"
        assert family.id != attr_src_family.id
        assert family_trigger.id != attr_src_family_trigger.id


def test_provenance():
    doc = _get_doc()
    sentences = doc.get_annotations_by_label("sentence")
    targets = doc.get_annotations_by_label("disease")

    prov_tracer = ProvTracer()
    propagator_1 = AttributeDuplicator(attr_labels=["is_family"])
    propagator_1.set_prov_tracer(prov_tracer)

    # is_family was 'detected' in sentences
    propagator_1.run(sentences, targets)

    sentence_attr_1 = sentences[0].get_attrs_by_label("is_family")[0]
    attr_1 = targets[0].get_attrs_by_label("is_family")[0]

    attr_1_prov = prov_tracer.get_prov(attr_1.id)
    assert attr_1_prov.data_item == attr_1
    assert attr_1_prov.op_desc == propagator_1.description
    assert attr_1_prov.source_data_items == [sentence_attr_1]
