import pytest
from numpy.testing import assert_almost_equal

from medkit.core import Attribute
from medkit.core.text import TextDocument
from medkit.text.metrics.classification import TextClassificationEvaluator

_TXT_1 = "Compte de rendu"
_TXT_2 = "Report d'urgences"
_LABEL_ATTR = "type_note"
_METADATA_KEY = "file_id"


@pytest.fixture()
def true_documents():
    return [
        TextDocument(
            _TXT_1,
            attrs=[Attribute(label=_LABEL_ATTR, value="CR")],
            metadata={_METADATA_KEY: "DOC0"},
        ),
        TextDocument(
            _TXT_2,
            attrs=[Attribute(label=_LABEL_ATTR, value="URG")],
            metadata={_METADATA_KEY: "DOC1"},
        ),
    ]


@pytest.fixture()
def evaluator():
    return TextClassificationEvaluator(
        attr_label=_LABEL_ATTR, metadata_key=_METADATA_KEY
    )


_PREDICTED_VALUES_BY_CASE = {
    "perfect_prediction": [
        TextDocument(
            _TXT_1,
            attrs=[Attribute(label=_LABEL_ATTR, value="CR")],
            metadata={_METADATA_KEY: "DOC0"},
        ),
        TextDocument(
            _TXT_2,
            attrs=[Attribute(label=_LABEL_ATTR, value="URG")],
            metadata={_METADATA_KEY: "DOC1"},
        ),
    ],
    "one_missing": [
        TextDocument(
            _TXT_1,
            attrs=[Attribute(label=_LABEL_ATTR, value="URG")],
            metadata={_METADATA_KEY: "DOC0"},
        ),
        TextDocument(
            _TXT_2,
            attrs=[Attribute(label=_LABEL_ATTR, value="URG")],
            metadata={_METADATA_KEY: "DOC1"},
        ),
    ],
    "incorrect_prediction": [
        TextDocument(
            _TXT_1,
            attrs=[Attribute(label=_LABEL_ATTR, value="URG")],
            metadata={_METADATA_KEY: "DOC0"},
        ),
        TextDocument(
            _TXT_2,
            attrs=[Attribute(label=_LABEL_ATTR, value="CR")],
            metadata={_METADATA_KEY: "DOC1"},
        ),
    ],
}

TEST_DATA = [
    (
        _PREDICTED_VALUES_BY_CASE["perfect_prediction"],
        {
            "overall_precision": 1.0,
            "overall_recall": 1.0,
            "overall_f1-score": 1.0,
            "overall_acc": 1.0,
            "overall_support": 2,
        },
    ),
    (
        _PREDICTED_VALUES_BY_CASE["one_missing"],
        {
            "overall_precision": 0.25,
            "overall_recall": 0.5,
            "overall_f1-score": 0.33,
            "overall_acc": 0.5,
            "overall_support": 2,
        },
    ),
    (
        _PREDICTED_VALUES_BY_CASE["incorrect_prediction"],
        {
            "overall_precision": 0.0,
            "overall_recall": 0.0,
            "overall_f1-score": 0.0,
            "overall_acc": 0.0,
            "overall_support": 2,
        },
    ),
]


@pytest.mark.parametrize(
    "predicted_docs,expected_metrics",
    TEST_DATA,
    ids=[
        "perfect_prediction",
        "one_missing",
        "incorrect_prediction",
    ],
)
def test_classification_report(
    evaluator: TextClassificationEvaluator,
    true_documents,
    predicted_docs,
    expected_metrics,
):
    metrics = evaluator.compute_classification_repport(
        true_docs=true_documents,
        predicted_docs=predicted_docs,
        metrics_by_attr_value=False,
    )

    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)


def test_classification_report_by_attr_value(
    evaluator: TextClassificationEvaluator, true_documents
):
    predicted_docs = _PREDICTED_VALUES_BY_CASE["one_missing"]
    metrics = evaluator.compute_classification_repport(
        true_docs=true_documents,
        predicted_docs=predicted_docs,
        metrics_by_attr_value=True,
    )
    expected_metrics = {
        "overall_precision": 0.25,
        "overall_recall": 0.5,
        "overall_f1-score": 0.33,
        "overall_support": 2,
        "overall_acc": 0.5,
        "CR_precision": 0,
        "CR_recall": 0,
        "CR_f1-score": 0,
        "CR_support": 1,
        "URG_precision": 0.5,
        "URG_recall": 1.0,
        "URG_f1-score": 0.67,
        "URG_support": 1,
    }

    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)


TEST_DATA_CK = [
    (_PREDICTED_VALUES_BY_CASE["perfect_prediction"], {"cohen_kappa": 1, "support": 2}),
    (_PREDICTED_VALUES_BY_CASE["one_missing"], {"cohen_kappa": 0, "support": 2}),
    (
        _PREDICTED_VALUES_BY_CASE["incorrect_prediction"],
        {"cohen_kappa": -1, "support": 2},
    ),
]


@pytest.mark.parametrize(
    "predicted_docs,expected_metrics",
    TEST_DATA_CK,
    ids=[
        "total_agreement",
        "partial_agreement",
        "chance_agreement",
    ],
)
def test_cohen_kappa(
    evaluator: TextClassificationEvaluator,
    true_documents,
    predicted_docs,
    expected_metrics,
):
    metrics = evaluator.compute_cohen_kappa(true_documents, predicted_docs)
    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)
