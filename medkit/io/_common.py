from collections import defaultdict
import logging
from typing import DefaultDict, List, Optional
from medkit.core.text import TextDocument, Segment, Entity, Relation, TextAnnotation

logger = logging.getLogger(__name__)


def get_anns_by_type(
    medkit_doc: TextDocument, anns_labels: Optional[List[str]]
) -> DefaultDict[str, TextAnnotation]:
    """Filter annotation by labels and return a dict by type of annotation"""
    anns_by_type = defaultdict(list)
    annotations = medkit_doc.anns.get()

    if anns_labels is not None:
        # filter annotations by label
        annotations = [ann for ann in annotations if ann.label in anns_labels]
        if anns_labels and annotations == []:
            # labels_anns were a list but none of the annotations
            # had a label of interest
            labels_str = ",".join(anns_labels)
            logger.info(
                f"No medkit annotations were included because none have '{labels_str}'"
                " as label."
            )

    for ann in annotations:
        if isinstance(ann, Entity):
            anns_by_type["entities"].append(ann)
        elif isinstance(ann, Relation):
            anns_by_type["relations"].append(ann)
        elif isinstance(ann, Segment):
            anns_by_type["segments"].append(ann)
    return anns_by_type
