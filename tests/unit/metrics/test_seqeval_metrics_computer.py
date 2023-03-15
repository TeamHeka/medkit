import pytest
import torch
from numpy.testing import assert_almost_equal

from medkit.metrics import SeqEvalMetricsComputer
from medkit.training import BatchData


def _mock_model_output(nb_tokens, nb_labels, predicted_labels_ids):
    # create a BatchData with a tensor called 'logits'
    # put 1 in the desired column to mock prediction
    logits = torch.zeros((1, nb_tokens, nb_labels))
    for i, j in enumerate(predicted_labels_ids):
        logits[0, i, j] = 1

    model_output = BatchData({"logits": logits})
    return model_output


@pytest.fixture(scope="module")
def input_batch():
    # input batch representing "medkit is a python library"
    # two entities: medkit and python
    # labels only in the first token
    input_batch = BatchData(
        {
            "input_ids": torch.tensor(
                [[101, 19960, 23615, 2003, 1037, 18750, 3075, 102]]
            ),
            "attention_masks": torch.tensor([[1, 1, 1, 1, 1, 1, 1, 1]]),
            "labels": torch.tensor([[-100, 1, -100, 0, 0, 3, 0, -100]]),
            "ref_labels_tags": [["B-corporation", "O", "O", "B-language", "O"]],
        }
    )
    return input_batch


@pytest.fixture(scope="module")
def id_to_label_bio():
    id_to_label = {
        0: "O",
        1: "B-corporation",
        2: "I-corporation",
        3: "B-language",
        4: "I-language",
    }
    return id_to_label


TEST_DATA = [
    (
        [0, 1, 0, 0, 0, 3, 0, 0],
        [["B-corporation", "O", "O", "B-language", "O"]],
        {
            "overall_precision": 1.0,
            "overall_recall": 1.0,
            "overall_f1-score": 1.0,
            "overall_acc": 1.0,
            "overall_support": 2,
        },
    ),
    (
        [0, 1, 0, 0, 2, 3, 0, 0],
        [["B-corporation", "O", "I-corporation", "B-language", "O"]],
        {
            "overall_precision": 0.66,
            "overall_recall": 1.0,
            "overall_f1-score": 0.8,
            "overall_acc": 0.8,
            "overall_support": 2,
        },
    ),
    (
        [0, 0, 0, 4, 4, 0, 1, 0],
        [["O", "I-language", "I-language", "O", "B-corporation"]],
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
    "mock_pred_labels_ids,expected_tags,expected_metrics",
    TEST_DATA,
    ids=[
        "perfect_prediction",
        "one_missing",
        "none_prediction",
    ],
)
def test_seqeval_metrics_computer_bio(
    input_batch, id_to_label_bio, mock_pred_labels_ids, expected_tags, expected_metrics
):
    # Testing behaviour with BIO TAGS, returning only overall metrics
    # mock model_output data shape (1,nb_tokens,nb_labels)
    nb_tokens = len(input_batch[0]["labels"])
    nb_labels = len(id_to_label_bio)
    model_output = _mock_model_output(
        nb_tokens=nb_tokens,
        nb_labels=nb_labels,
        predicted_labels_ids=mock_pred_labels_ids,
    )

    # define the metrics computer with BIO scheme, no entities metrics
    use_bilou_scheme = False
    metrics_computer = SeqEvalMetricsComputer(
        id_to_label=id_to_label_bio,
        use_bilou_scheme=use_bilou_scheme,
        return_entity_metrics=False,
    )

    # prepare batch for the metric
    prepared_data = metrics_computer.prepare_batch(
        input_batch=input_batch, model_output=model_output
    )

    assert prepared_data["y_true"] == input_batch["ref_labels_tags"]
    assert prepared_data["y_pred"] == expected_tags

    metrics = metrics_computer.compute(prepared_data)

    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)


def test_seqeval_metrics_with_entities(input_batch, id_to_label_bio):
    # Testing behaviour with BIO TAGS, returning overall and entity metrics
    # mock model_output data shape (1,nb_tokens,nb_labels)
    nb_tokens = len(input_batch[0]["labels"])
    nb_labels = len(id_to_label_bio)
    model_output = _mock_model_output(
        nb_tokens=nb_tokens,
        nb_labels=nb_labels,
        predicted_labels_ids=[0, 1, 0, 0, 2, 3, 0, 0],
    )

    # define the metrics computer with BIO scheme with entities metrics
    use_bilou_scheme = False
    metrics_computer = SeqEvalMetricsComputer(
        id_to_label=id_to_label_bio,
        use_bilou_scheme=use_bilou_scheme,
        return_entity_metrics=True,
    )

    # prepare batch for the metric
    prepared_data = metrics_computer.prepare_batch(
        input_batch=input_batch, model_output=model_output
    )

    expected_tags = [["B-corporation", "O", "I-corporation", "B-language", "O"]]
    assert prepared_data["y_true"] == input_batch["ref_labels_tags"]
    assert prepared_data["y_pred"] == expected_tags

    expected_metrics = {
        "overall_precision": 0.66,
        "overall_recall": 1.0,
        "overall_f1-score": 0.8,
        "overall_support": 2,
        "overall_acc": 0.8,
        "corporation_precision": 0.5,
        "corporation_recall": 1.0,
        "corporation_f1-score": 0.66,
        "corporation_support": 1,
        "language_precision": 1.0,
        "language_recall": 1.0,
        "language_f1-score": 1.0,
        "language_support": 1,
    }

    metrics = metrics_computer.compute(prepared_data)

    assert len(metrics.keys()) == len(expected_metrics.keys())
    for metric_key, value in expected_metrics.items():
        assert metric_key in metrics
        assert_almost_equal(metrics[metric_key], value, decimal=2)


def test_seqeval_metrics_bilou():
    # Testing behaviour with BILOU TAGS, returning overall and entity metrics
    # Mock input values
    # input batch representing "medkit"
    # one entity: medkit
    # labels all tokens with bilou scheme
    input_batch = BatchData(
        {
            "input_ids": torch.tensor([[101, 19960, 23615, 102]]),
            "attention_masks": torch.tensor([[1, 1, 1, 1]]),
            "labels": torch.tensor([[-100, 1, 3, -100]]),
            "ref_labels_tags": [["B-corporation", "L-corporation"]],
        }
    )
    # labels with bilou tags
    id_to_label_bilou = {
        0: "O",
        1: "B-corporation",
        2: "I-corporation",
        3: "L-corporation",
        5: "U-corporation",
    }

    # getting shape of model output
    nb_tokens = len(input_batch[0]["labels"])
    nb_labels = len(id_to_label_bilou)

    # define the metrics computer using bilou tags
    use_bilou_scheme = True
    metrics_computer = SeqEvalMetricsComputer(
        id_to_label=id_to_label_bilou,
        use_bilou_scheme=use_bilou_scheme,
        return_entity_metrics=True,
    )

    # testing perfect match
    expected_tags = [["B-corporation", "L-corporation"]]
    model_output = _mock_model_output(
        nb_labels=nb_labels, nb_tokens=nb_tokens, predicted_labels_ids=[0, 1, 3, 0]
    )

    # prepare batch for the metric
    prepared_data = metrics_computer.prepare_batch(
        input_batch=input_batch, model_output=model_output
    )

    assert prepared_data["y_true"] == input_batch["ref_labels_tags"]
    assert prepared_data["y_pred"] == expected_tags

    metrics = metrics_computer.compute(prepared_data)
    assert_almost_equal(metrics["overall_precision"], 1.0, decimal=2)
    assert_almost_equal(metrics["corporation_precision"], 1.0, decimal=2)

    # testing one missing, bilou is strict match
    expected_tags = [["B-corporation", "I-corporation"]]
    model_output = _mock_model_output(
        nb_labels=nb_labels, nb_tokens=nb_tokens, predicted_labels_ids=[0, 1, 2, 0]
    )

    # prepare batch for the metric
    prepared_data = metrics_computer.prepare_batch(
        input_batch=input_batch, model_output=model_output
    )

    assert prepared_data["y_true"] == input_batch["ref_labels_tags"]
    assert prepared_data["y_pred"] == expected_tags

    metrics = metrics_computer.compute(prepared_data)

    assert_almost_equal(metrics["overall_precision"], 0.0, decimal=2)
    assert_almost_equal(metrics["corporation_precision"], 0.0, decimal=2)
