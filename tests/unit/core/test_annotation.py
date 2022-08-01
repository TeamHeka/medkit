import pytest

from medkit.core.annotation import Annotation, Attribute


_NEGATION_ATTR = Attribute(label="negation", value=False)
_CUI_ATTR_1 = Attribute(label="cui", value="C0011854")
_CUI_ATTR_2 = Attribute(label="cui", value="C0011855")


def test_add_attrs():
    ann = Annotation(label="problem")

    assert len(ann.get_attrs()) == 0
    assert len(ann.get_attrs_by_label("cui")) == 0
    assert len(ann.get_attrs_by_label("negation")) == 0

    ann.add_attr(_NEGATION_ATTR)
    ann.add_attr(_CUI_ATTR_1)
    ann.add_attr(_CUI_ATTR_2)

    assert ann.get_attrs() == [_NEGATION_ATTR, _CUI_ATTR_1, _CUI_ATTR_2]
    assert ann.get_attrs_by_label("negation") == [_NEGATION_ATTR]
    assert ann.get_attrs_by_label("cui") == [_CUI_ATTR_1, _CUI_ATTR_2]


def test_attrs_at_init():
    attrs = [_NEGATION_ATTR, _CUI_ATTR_1, _CUI_ATTR_2]
    ann = Annotation(label="problem", attrs=attrs)

    assert ann.get_attrs() == attrs
    assert ann.get_attrs_by_label("negation") == [_NEGATION_ATTR]
    assert ann.get_attrs_by_label("cui") == [_CUI_ATTR_1, _CUI_ATTR_2]


def test_add_same_attr():
    ann = Annotation(label="problem")
    ann.add_attr(_CUI_ATTR_1)

    with pytest.raises(
        ValueError, match="Attribute with id .* already attached to annotation"
    ):
        ann.add_attr(_CUI_ATTR_1)
