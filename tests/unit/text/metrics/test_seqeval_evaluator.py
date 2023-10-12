import pytest
from numpy.testing import assert_almost_equal

pytest.importorskip(modname="seqeval", reason="seqeval is not installed")
pytest.importorskip(modname="transformers", reason="transformers is not installed")

from transformers import BertTokenizerFast  # noqa: E402

from medkit.core.text import Entity, TextDocument, Span  # noqa: E402
from medkit.text.metrics.ner import SeqEvalEvaluator  # noqa: E402
from tests.data_utils import get_path_hf_dummy_vocab  # noqa: E402


@pytest.fixture()
def document():
    document = TextDocument(
        text="medkit is a python library",
        anns=[
            Entity(label="corporation", spans=[Span(start=0, end=6)], text="medkit"),
            Entity(label="language", spans=[Span(start=12, end=18)], text="python"),
        ],
    )
    return document


_PREDICTED_ENTS_BY_CASE = {
    "perfect_prediction": [
        Entity(label="corporation", spans=[Span(start=0, end=6)], text="medkit"),
        Entity(label="language", spans=[Span(start=12, end=18)], text="python"),
    ],
    "one_missing": [
        Entity(label="corporation", spans=[Span(start=0, end=6)], text="medkit"),
        Entity(label="language", spans=[Span(start=10, end=16)], text="a pyth"),
    ],
    "incorrect_prediction": [
        Entity(label="misc", spans=[Span(start=19, end=23)], text="lib "),
    ],
}


TEST_DATA = [
    (
        _PREDICTED_ENTS_BY_CASE["perfect_prediction"],
        {
            "overall_precision": 1.0,
            "overall_recall": 1.0,
            "overall_f1-score": 1.0,
            "overall_acc": 1.0,
            "overall_support": 2,
        },
    ),
    (
        _PREDICTED_ENTS_BY_CASE["one_missing"],
        {
            "overall_precision": 0.5,
            "overall_recall": 0.5,
            "overall_f1-score": 0.5,
            "overall_acc": 0.8,
            "overall_support": 2,
        },
    ),
    (
        _PREDICTED_ENTS_BY_CASE["incorrect_prediction"],
        {
            "overall_precision": 0.0,
            "overall_recall": 0.0,
            "overall_f1-score": 0.0,
            "overall_acc": 0.38,  # there is 14 'O' in GT, 4 were tagged with 'misc' so, 10/26
            "overall_support": 2,
        },
    ),
]


@pytest.mark.parametrize(
    "predicted_entities,expected_metrics",
    TEST_DATA,
    ids=[
        "perfect_prediction",
        "one_missing",
        "incorrect_prediction",
    ],
)
def test_evaluator_bio(document, predicted_entities, expected_metrics):
    # define an evaluator with IOB2 scheme, no entities metrics
    tagging_scheme = "iob2"
    evaluator = SeqEvalEvaluator(
        tokenizer=None, tagging_scheme=tagging_scheme, return_metrics_by_label=False
    )
    metrics = evaluator.compute(
        documents=[document], predicted_entities=[predicted_entities]
    )
    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)


@pytest.mark.parametrize(
    "tagging_scheme,expected_accuracy",
    [("iob2", 0.80), ("bilou", 0.76)],
)
def test_evaluator_with_entities_all_schemes(
    document, tagging_scheme, expected_accuracy
):
    # only accuracy changes with the scheme
    # testing with two entities, one incorrect
    predicted_entities = _PREDICTED_ENTS_BY_CASE["one_missing"]

    evaluator = SeqEvalEvaluator(
        tokenizer=None, tagging_scheme=tagging_scheme, return_metrics_by_label=True
    )
    metrics = evaluator.compute(
        documents=[document], predicted_entities=[predicted_entities]
    )
    expected_metrics = {
        "overall_precision": 0.5,
        "overall_recall": 0.5,
        "overall_f1-score": 0.5,
        "overall_support": 2,
        "overall_acc": expected_accuracy,
        "corporation_precision": 1.0,
        "corporation_recall": 1.0,
        "corporation_f1-score": 1.0,
        "corporation_support": 1,
        "language_precision": 0.0,
        "language_recall": 0.0,
        "language_f1-score": 0.0,
        "language_support": 1,
    }
    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)


@pytest.mark.parametrize(
    "tagging_scheme,expected_accuracy",
    [("iob2", 0.75), ("bilou", 0.75)],
)
def test_evaluator_with_bert_tokenizer(document, tagging_scheme, expected_accuracy):
    # testing with a bert tokenizer two entities, one incorrect
    predicted_entities = _PREDICTED_ENTS_BY_CASE["one_missing"]
    tokenizer = BertTokenizerFast(get_path_hf_dummy_vocab())
    evaluator = SeqEvalEvaluator(
        tokenizer=tokenizer,
        tagging_scheme=tagging_scheme,
        return_metrics_by_label=True,
    )
    metrics = evaluator.compute(
        documents=[document], predicted_entities=[predicted_entities]
    )
    expected_metrics = {
        "overall_precision": 0.5,
        "overall_recall": 0.5,
        "overall_f1-score": 0.5,
        "overall_support": 2,
        "overall_acc": expected_accuracy,
        "corporation_precision": 1.0,
        "corporation_recall": 1.0,
        "corporation_f1-score": 1.0,
        "corporation_support": 1,
        "language_precision": 0.0,
        "language_recall": 0.0,
        "language_f1-score": 0.0,
        "language_support": 1,
    }
    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)
