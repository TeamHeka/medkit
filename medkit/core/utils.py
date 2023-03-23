__all__ = ["batch_iter", "batch_list", "modules_are_available"]

import importlib.util
from typing import Any, Iterator, List


def batch_iter(iter: Iterator[Any], batch_size: int) -> Iterator[List[Any]]:
    """Group values yielded by an iterator into batches.

    Parameters
    ----------
    iter:
        The iterator yielding values to batch.
    batch_size:
        Length of batches (the last batch may be smaller).

    Returns
    -------
    Iterator[List[Any]]:
        Iterator yielding lists of `batch_size` items (the last list yielded may
        be smaller).
    """
    while True:
        batch = []
        for _ in range(batch_size):
            try:
                batch.append(next(iter))
            except StopIteration:
                yield batch
                return
        yield batch


def batch_list(list: List[Any], batch_size: int) -> Iterator[List[Any]]:
    """Split list into smaller batches.

    Parameters
    ----------
    list:
        The list containing values to batch.
    batch_size:
        Length of batches (the last batch may be smaller).

    Returns
    -------
    Iterator[List[Any]]:
        Iterator yielding lists of `batch_size` items (the last list yielded may
        be smaller).
    """
    for i in range(0, len(list), batch_size):
        yield list[i : i + batch_size]


def modules_are_available(modules: List[str]):
    return all(importlib.util.find_spec(m) is not None for m in modules)
