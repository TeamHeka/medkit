"""Metrics to assess inter-annotator agreement"""
__all__ = ["cohen_kappa", "krippendorff_alpha"]
from typing import List, Union
import numpy as np


def _check_len_labels(*all_labels):
    lengths = set(len(labels) for labels in all_labels)
    if len(lengths) > 1:
        raise ValueError(
            f"The lists have different sizes. The lists found have {lengths} as their"
            " lengths"
        )


def cohen_kappa(
    tags_rater1: List[Union[str, int]], tags_rater2: List[Union[str, int]]
) -> float:
    """
    Compute Cohen's kappa: a coefficient of agreement between two annotators.

    This function computes Cohen's kappa [1]_ for qualitative data. It measures
    the agreement between two annotators who classify `n` items in `n_labels`.

    It could be defined in terms of numbers of agreements and number of classified items.

    .. math::
        \\kappa = \\frac{n_a - n_e}{n - n_e}

    where :math:`n_a` is the number of agreements, :math:`n_e` is the sum of
    agreements by chance and :math:`n` is the number of classified items [2]_.

    Parameters
    ----------
    tags_rater1 : list of (n_samples,)
        Labels assigned by the first annotator

    tags_rater2 : list of (n_samples,)
        Labels assigned by the second annotator

    Returns
    -------
    kappa : float
        The kappa coefficient, a number between -1 and 1.
        A value of 0 indicates no aggrement between annotators, and
        a value of 1 indicates perfect agreement. This coefficient is
        sensitive to imbalanced data.

    Raises
    ------
    ValueError
        Raise if `tags_rater1` or `tags_rater2` differs in size

    References
    ----------
    .. [1] J. Cohen, "A Coefficient of Agreement for Nominal Scales",
            Educational and Psychological Measurement, vol. 20, no. 1,
            pp. 37-46, 1960, doi: 10.1177/001316446002000104.
    .. [2] C. Geisler and J. Swarts, Coding Streams of Language: Techniques
            for the Systematic Coding of Text, Talk, and Other Verbal Data.
            The WAC Clearinghouse University Press of Colorado, 2019,
            pp. 162-164. doi: 10.37514/pra-b.2019.0230."""

    _check_len_labels(tags_rater1, tags_rater2)

    labels = set(tags_rater1).union(set(tags_rater2))
    label_to_int = {label: i for i, label in enumerate(labels)}
    y1 = np.array([label_to_int[x] for x in tags_rater1])
    y2 = np.array([label_to_int[x] for x in tags_rater2])

    n_items = len(y1)
    n_agreements = np.sum(y1 == y2)

    # count number of occurrences of each label
    n1_by_label = np.bincount(y1)
    n2_by_label = np.bincount(y2)
    n_expected = np.sum(n1_by_label * n2_by_label) / n_items
    kappa = np.clip((n_agreements - n_expected) / (n_items - n_expected), -1, 1)
    return kappa


def _get_values_by_unit_matrix(
    reliability_data: np.ndarray, labels_set: np.ndarray
) -> np.ndarray:
    """
    Return the label counts given the annotators_data.

    Parameters
    ----------
    reliability_data : ndarray, with shape (m_annotators, n_samples)
        numpy array with labels given to `n_samples` by `m_annotators`
        The missing labels are represented with `None`.

    labels_set : ndarray, with shape (n_labels,)
        Possible labels the item can take.

    Returns
    -------
    values_by_unit : ndarray, with shape (n_labels, n_samples)
        Number of annotators that assigned a certain label by annotation.
        Where `n_labels` is the number of possible labels and `n_samples`
        is the number of annotations.
    """
    ann_data_expanded = np.expand_dims(reliability_data, 2)
    return np.sum(ann_data_expanded == labels_set, axis=0).T


def _compute_observed_disagreement(values_by_unit_matrix: np.ndarray) -> float:
    """
    Return the observed disagreement given values-by-unit matrix.

    Parameters
    ----------
    values_by_unit_matrix : ndarray, with shape (n_labels, n_samples)
        Count of annotators that assigned a certain label by annotation.

    Returns
    -------
    do : float
        observed disagreement among labels assigned to annotations
    """
    # select only units with disagreement
    # units with more than two assigned values
    units_to_keep = np.count_nonzero(values_by_unit_matrix, 0) > 1
    matrix_disagreement = values_by_unit_matrix[:, units_to_keep]
    total_by_unit = matrix_disagreement.sum(0)

    do = 0
    for u, unit in enumerate(matrix_disagreement.T):
        unit = unit[unit > 0]
        for n in range(0, len(unit)):
            # only nominal weight is supported in this function
            p_unit = np.dot(unit[n], unit[n + 1 :]) / (total_by_unit[u] - 1)
            do += np.sum(p_unit)
    return do


def _compute_expected_disagreement(values_by_unit_matrix: np.ndarray) -> float:
    """
    Return the expected disagreement given values-by-unit matrix.

    Parameters
    ----------
    values_by_unit_matrix : ndarray, with shape (n_labels, n_samples)
        Count of annotators that assigned a certain label by annotation.

    Returns
    -------
    de : float
        expected disagreement annotators will have by chance
    """
    # all units with at least 1 value
    paried_units = values_by_unit_matrix.sum(0) > 1
    total_by_value = values_by_unit_matrix[:, paried_units].sum(1)

    de = 0
    # only nominal weight is supported in this function
    for n_c in range(0, len(total_by_value) - 1):
        de += np.sum(np.dot(total_by_value[n_c], total_by_value[n_c + 1 :]))
    return de


def krippendorff_alpha(all_annotators_data: List[List[Union[None, str, int]]]) -> float:
    """
    Compute Krippendorff's alpha: a coefficient of agreement among many
    annotators.

    This coefficient is a generalization of several reliability indices.
    The general form is:

    .. math::
        \\alpha = 1 - \\frac{D_o}{D_e}

    where :math:`D_o` is the observed disagreement among labels assigned to
    units or annotations and :math:`D_e` is the disagreement between annotators
    attributable to chance. The arguments of the disagreement measures are values
    in coincidence matrices.

    This function implements the general computational form proposed in [3]_,
    but only supports binaire or nominal labels.

    Parameters
    ----------
    all_annotators_data : array_like, (m_annotators,n_samples)
        Reliability_data, list or array of labels given to `n_samples` by `m_annotators`.
        Missing labels are represented with `None`

    Returns
    -------
    alpha : float
        The alpha coefficient, a number between 0 and 1.
        A value of 0 indicates the absence of reliability, and
        a value of 1 indicates perfect reliability.

    Raises
    ------
    ValueError
        Raise if any list of labels within `all_annotators_data` differs in size
    AssertionError
        Raise if `all_annotators_data` has only one label to be compared

    References
    ----------
    .. [3] K. Krippendorff, “Computing Krippendorff's alpha-reliability,”
            ScholarlyCommons, 25-Jan-2011, pp. 8-10. [Online].
            Available: https://repository.upenn.edu/asc_papers/43/

    Examples
    --------
    Three annotators labelled six items. Some labels are missing.

    >>> annotator_A = ['yes','yes','no','no','yes',None]
    >>> annotator_B = [None,'yes','no','yes','yes','no']
    >>> annotator_C = ['yes','no','no','yes','yes',None]
    >>> krippendorff_alpha([annotator_A,annotator_B,annotator_C])
    0.42222222222222217
    """
    _check_len_labels(*all_annotators_data)

    all_annotators_data = np.asarray(all_annotators_data)
    labels_set = [cat for cat in set(all_annotators_data.flatten()) if cat is not None]

    assert len(labels_set) > 1, "There must be more than one label in annotators data"

    values_count = _get_values_by_unit_matrix(all_annotators_data, labels_set)
    do = _compute_observed_disagreement(values_count)
    de = _compute_expected_disagreement(values_count)
    total_paried_values = np.sum(values_count[:, values_count.sum(0) > 1])

    alpha = 1 - (total_paried_values - 1) * (do / de)
    return alpha
