import pytest
from numpy.testing import assert_almost_equal

from medkit.text.metrics._irr_utils import krippendorff_alpha, cohen_kappa


def test_krippendorff_alpha():
    # data from Krippendorff,K.(2011)
    # binary data, two annotators, no missing data
    annotator1 = [0, 1, 0, 0, 0, 0, 0, 0, 1, 0]
    annotator2 = [1, 1, 1, 0, 0, 1, 0, 0, 0, 0]

    alpha = krippendorff_alpha([annotator1, annotator2])
    assert_almost_equal(alpha, 0.095, decimal=3)
    assert alpha == krippendorff_alpha([annotator2, annotator1])

    # nominal data, two annotators, no mising data
    annotator1 = ["a", "a", "b", "b", "d", "c", "c", "c", "e", "d", "d", "a"]
    annotator2 = ["b", "a", "b", "b", "b", "c", "c", "c", "e", "d", "d", "d"]
    alpha = krippendorff_alpha([annotator1, annotator2])
    assert_almost_equal(alpha, 0.692, decimal=3)
    assert alpha == krippendorff_alpha([annotator2, annotator1])

    # nominal data, any number of annotators, missing data
    A = [1, 2, 3, 3, 2, 1, 4, 1, 2, None, None, None]
    B = [1, 2, 3, 3, 2, 2, 4, 1, 2, 5, None, 3]
    C = [None, 3, 3, 3, 2, 3, 4, 2, 2, 5, 1, None]
    D = [1, 2, 3, 3, 2, 4, 4, 1, 2, 5, 1, None]
    alpha = krippendorff_alpha([A, B, C, D])
    assert_almost_equal(alpha, 0.743, decimal=3)
    assert alpha == krippendorff_alpha([D, C, B, A])
    assert alpha == krippendorff_alpha([D, A, C, B])

    # testing exceptions
    with pytest.raises(
        ValueError, match="The lists have different sizes. The lists found have .*"
    ):
        krippendorff_alpha([[1, 2, 1], [1, 2, 1] * 2])

    with pytest.raises(AssertionError, match="There must be more than one .*"):
        krippendorff_alpha([[1, 1, 1], [1, 1, 1]])


def test_cohen_kappa():
    # data from C. Geisler and J. Swarts (2019)
    # nominal data, two annotators
    raw_y1 = (
        "business user business "
        + "system " * 3
        + "team system business user system "
        + "user " * 4
        + "system"
    )
    raw_y2 = (
        "business user business team system team team system business user system "
        + "user " * 4
        + "system"
    )
    y1 = raw_y1.split()
    y2 = raw_y2.split()
    kappa = cohen_kappa(y1, y2)
    assert_almost_equal(kappa, 0.83, decimal=2)
    assert kappa == cohen_kappa(y2, y1)

    # data from sklearn
    y_true = [2, 0, 2, 2, 0, 1]
    y_pred = [0, 0, 2, 2, 0, 2]
    kappa = cohen_kappa(y_true, y_pred)
    assert_almost_equal(kappa, 0.428, decimal=3)
    assert kappa == cohen_kappa(y_pred, y_true)

    # testing exceptions
    with pytest.raises(
        ValueError, match="The lists have different sizes. The lists found have .*"
    ):
        cohen_kappa([1, 2], [1])
