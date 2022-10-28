"""Metrics to assess inter-annotator agreement"""
from typing import List, Union
import numpy as np


def _check_len_labels(*all_labels):
    lengths = set(len(labels) for labels in all_labels)
    if len(lengths) > 1:
        raise ValueError("The lists have different sizes")


def cohen_kappa(y1: List[Union[str, int]], y2: List[Union[str, int]]) -> float:
    """
    Compute Cohen's kappa: a coefficient of agreement between two annotators.

    This function computes Cohen's kappa [1] for qualitative data. It measures
    the agreement between two annotators who classify `n` items in `C` labels.

    It could be defined in terms of numbers of agreements and number of classified items.

    .. math::
        \\kappa = (n_a - n_e) / (n - n_e)

    where :math:`n_a` is the number of agreements, :math:`n_e` is the sum of
    agreements by chance and :math:`n` is the number of classified items [2].

    Parameters
    ----------
    y1 : list of (n_samples,)
        Labels assigned by the first annotator

    y2 : list of (n_samples,)
        Labels assigned by the second annotator

    Returns
    -------
    kappa : float
        The kappa coefficient, a number between -1 and 1.
        A value of 0 indicates no aggrement between annotators, and
        a value of 1 indicates perfect agreement. This coefficient is
        sensitive to imbalanced data.

    References
    ----------
    .. [1] J. Cohen, "A Coefficient of Agreement for Nominal Scales",
            Educational and Psychological Measurement, vol. 20, no. 1,
            pp. 37-46, 1960, doi: 10.1177/001316446002000104.
    .. [2] C. Geisler and J. Swarts, Coding Streams of Language: Techniques
            for the Systematic Coding of Text, Talk, and Other Verbal Data.
            The WAC Clearinghouse University Press of Colorado, 2019,
            pp. 162-164. doi: 10.37514/pra-b.2019.0230."""

    _check_len_labels(y1, y2)

    labels = set(y1 + y2)
    label_to_int = {label: i for i, label in enumerate(labels)}
    y1 = np.array([label_to_int[x] for x in y1])
    y2 = np.array([label_to_int[x] for x in y2])

    n_items = len(y1)
    n_agreements = np.sum(y1 == y2)

    # count number of occurrences of each label
    n1_by_label = np.bincount(y1)
    n2_by_label = np.bincount(y2)
    n_expected = np.sum(n1_by_label * n2_by_label) / n_items

    kappa = (n_agreements - n_expected) / (n_items - n_expected)
    return kappa
