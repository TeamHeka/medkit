import pytest

from medkit.core import Attribute, ProvBuilder
from medkit.core.text import Segment, Span
from medkit.text.ner.duckling_matcher import DucklingMatcher

_TEXT = "The patient was admitted on 01/02/2001 and stayed for 3 days before leaving"

_TIME_VALUE = {
    "grain": "day",
    "type": "value",
    "value": "2001-01-02T00:00:00.000-08:00",
    "values": [
        {"grain": "day", "type": "value", "value": "2001-01-02T00:00:00.000-08:00"}
    ],
}

_DURATION_VALUE = {
    "value": 3,
    "day": 3,
    "type": "value",
    "unit": "day",
    "normalized": {"value": 259200, "unit": "second"},
}

_TIME_RESPONSE_DATA = {
    "dim": "time",
    "body": "on 01/02/2001",
    "start": 25,
    "end": 38,
    "value": _TIME_VALUE,
}

_DURATION_RESPONSE_DATA = {
    "dim": "duration",
    "body": "3 days",
    "start": 54,
    "end": 60,
    "value": _DURATION_VALUE,
}


class _MockHTTPResponse:
    def __init__(self, data):
        self.status_code = 200
        self.data = data

    def json(self):
        return self.data


def _mock_requests_get(url):
    return _MockHTTPResponse(None)


def _mock_requests_post(url, data):
    if "dims" not in data:
        response_data = [_TIME_RESPONSE_DATA, _DURATION_RESPONSE_DATA]
    else:
        response_data = []
        if "time" in data["dims"]:
            response_data.append(_TIME_RESPONSE_DATA)
        if "duration" in data["dims"]:
            response_data.append(_DURATION_RESPONSE_DATA)
    return _MockHTTPResponse(response_data)


@pytest.fixture
def _mocked_requests(mocker):
    mocker.patch("requests.get", _mock_requests_get)
    mocker.patch("requests.post", _mock_requests_post)


def _get_sentence_segment(text=_TEXT):
    return Segment(
        label="sentence",
        spans=[Span(0, len(text))],
        text=text,
    )


def _find_entity(entities, label):
    try:
        return next(e for e in entities if e.label == label)
    except StopIteration:
        return None


def test_single_dim(_mocked_requests):
    sentence = _get_sentence_segment()

    matcher = DucklingMatcher(
        output_label="duckling",
        version="MOCK",
        locale="en",
        dims=["time"],
    )
    entities = matcher.run([sentence])

    # entity
    assert len(entities) == 1
    entity = _find_entity(entities, "time")
    assert entity is not None
    assert entity.text == "on 01/02/2001"
    assert entity.spans == [Span(25, 38)]

    # normalization attribute
    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "duckling"
    assert attr.value == _TIME_VALUE
    assert attr.metadata["version"] == "MOCK"


def test_multiple_dims(_mocked_requests):
    sentence = _get_sentence_segment()

    matcher = DucklingMatcher(
        output_label="duckling",
        version="MOCK",
        locale="en",
        dims=["time", "duration"],
    )
    entities = matcher.run([sentence])
    assert len(entities) == 2

    # 1st entity
    entity = _find_entity(entities, "time")
    assert entity is not None
    assert entity.text == "on 01/02/2001"
    assert entity.spans == [Span(25, 38)]

    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "duckling"
    assert attr.value == _TIME_VALUE

    # 2d entity
    assert len(entities) == 2
    entity = _find_entity(entities, "duration")
    assert entity is not None
    assert entity.text == "3 days"
    assert entity.spans == [Span(54, 60)]

    assert len(entity.attrs) == 1
    attr = entity.attrs[0]
    assert attr.label == "duckling"
    assert attr.value == _DURATION_VALUE


def test_all_dims(_mocked_requests):
    sentence = _get_sentence_segment()

    matcher = DucklingMatcher(
        output_label="duckling",
        version="MOCK",
        locale="en",
        dims=["time", "duration"],
    )
    entities = matcher.run([sentence])
    assert len(entities) == 2


def test_attrs_to_copy(_mocked_requests):
    sentence = _get_sentence_segment()
    # copied attribute
    sentence.attrs.append(Attribute(label="negation", value=True))
    # uncopied attribute
    sentence.attrs.append(Attribute(label="hypothesis", value=True))

    matcher = DucklingMatcher(
        output_label="duckling",
        version="MOCK",
        locale="en",
        dims=["time"],
        attrs_to_copy=["negation"],
    )
    entities = matcher.run([sentence])

    entity = _find_entity(entities, "time")
    assert len(entity.attrs) == 2
    attr = entity.attrs[0]
    assert attr.label == "negation" and attr.value is True


def test_prov(_mocked_requests):
    sentence = _get_sentence_segment()

    matcher = DucklingMatcher(
        output_label="duckling",
        version="MOCK",
        locale="en",
        dims=["time"],
    )
    entities = matcher.run([sentence])

    prov_builder = ProvBuilder()
    matcher.set_prov_builder(prov_builder)

    entities = matcher.run([sentence])
    graph = prov_builder.graph

    entity = _find_entity(entities, "time")
    entity_node = graph.get_node(entity.id)
    assert entity_node.data_item_id == entity.id
    assert entity_node.operation_id == matcher.id
    assert entity_node.source_ids == [sentence.id]

    attr = entity.attrs[0]
    attr_node = graph.get_node(attr.id)
    assert attr_node.data_item_id == attr.id
    assert attr_node.operation_id == matcher.id
    assert attr_node.source_ids == [sentence.id]
