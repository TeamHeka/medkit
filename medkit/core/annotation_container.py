__all__ = ["AnnotationContainer"]

import typing
from typing import Dict, Iterator, Generic, List, Optional, TypeVar

from medkit.core.annotation import Annotation
from medkit.core.store import Store, GlobalStore


AnnotationType = TypeVar("AnnotationType", bound=Annotation)


class AnnotationContainer(Generic[AnnotationType]):
    """
    Manage a list of annotations belonging to a document.

    This behaves more or less like a list: calling `len()` and iterating are
    supported. Additional filtering is available through the `get()` method.

    The annotations will be stored in a :class:`~medkit.core.Store`, which can
    rely on a simple dict or something more
    complicated like a database.

    This global store may be initialized using :class:~medkit.core.GlobalStore.
    Otherwise, a default one (i.e. dict store) is used.
    """

    def __init__(self):
        self._store: Store = GlobalStore.get_store()
        self._ann_ids: List[str] = []
        self._ann_ids_by_label: Dict[str, List[str]] = {}
        self._ann_ids_by_key: Dict[str, List[str]] = {}

    def add(self, ann: AnnotationType):
        """
        Attach an annotation to the document.

        Parameters
        ----------
        ann:
            Annotation to add.

        Raises
        ------
        ValueError
            If the annotation is already attached to the document
            (based on `annotation.uid`)
        """

        uid = ann.uid
        if uid in self._ann_ids:
            raise ValueError(
                f"Impossible to add this annotation.The uid {uid} already"
                " exists in the document"
            )

        self._ann_ids.append(uid)
        self._store.store_data_item(ann)

        # update label index
        label = ann.label
        if label not in self._ann_ids_by_label:
            self._ann_ids_by_label[label] = []
        self._ann_ids_by_label[label].append(uid)

        # update key index
        for key in ann.keys:
            if key not in self._ann_ids_by_key:
                self._ann_ids_by_key[key] = []
            self._ann_ids_by_key[key].append(uid)

    def __len__(self) -> int:
        """Add support for calling `len()`"""
        return len(self._ann_ids)

    def __iter__(self) -> Iterator[AnnotationType]:
        """
        Add support for iterating over an `AnnotationContainer` (will yield each
        attribute)
        """

        return iter(self.get_by_id(uid) for uid in self._ann_ids)

    def get(
        self, *, label: Optional[str] = None, key: Optional[str] = None
    ) -> List[AnnotationType]:
        """
        Return a list of the annotations of the document, optionally filtering
        by label or key.

        Parameters
        ----------
        label:
            Label to use to filter annotations.
        key:
            Key to use to filter annotations.
        """

        uids = self.get_ids(label=label, key=key)
        return [self.get_by_id(uid) for uid in uids]

    def get_ids(
        self, *, label: Optional[str] = None, key: Optional[str] = None
    ) -> Iterator[str]:
        """
        Return an iterator of the identifiers of the annotations of the
        document, optionally filtering by label or key.

        This method is provided, so it is easier to implement additional
        filtering in subclasses.

        Parameters
        ----------
        label:
            Label to use to filter annotations.
        key:
            Key to use to filter annotations.
        """

        uids = iter(self._ann_ids)

        if label is not None:
            uids = (uid for uid in uids if uid in self._ann_ids_by_label.get(label, []))

        if key is not None:
            uids = (uid for uid in uids if uid in self._ann_ids_by_key.get(key, []))

        return uids

    def get_by_id(self, uid: str) -> AnnotationType:
        """Return the annotation corresponding to a specific identifier.

        Parameters
        ----------
        uid:
            Identifier of the annotation to return.
        """

        ann = self._store.get_data_item(uid)
        return typing.cast(AnnotationType, ann)
