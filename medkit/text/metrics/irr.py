from collections import defaultdict
from typing import Dict, List, Optional
from medkit.core.text import TextDocument
from medkit.text.metrics._irr_utils import cohen_kappa, krippendorff_alpha
from medkit.text.metrics._common import DocumentAttrMetric, EntityAttrMetric


class DocumentAttrCohenKappa(DocumentAttrMetric):
    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        super().__init__(metadata_key, attr_label)

    def compute(
        self, docs_annotator_1: List[TextDocument], docs_annotator_2: List[TextDocument]
    ) -> Dict:
        ann1_tags_by_attr = self._format_docs_for_evaluation(docs_annotator_1)
        ann2_tags_by_attr = self._format_docs_for_evaluation(docs_annotator_2)

        common_attrs = set(ann1_tags_by_attr.keys()).intersection(
            ann2_tags_by_attr.keys()
        )
        all_scores = {}
        for attr in common_attrs:
            score = cohen_kappa(y1=ann1_tags_by_attr[attr], y2=ann2_tags_by_attr[attr])
            all_scores[attr] = {
                "cohen_kappa": score,
                "docs_support": len(ann1_tags_by_attr[attr]),
            }

        return all_scores


class EntityAttrCohenKappa(EntityAttrMetric):
    # backend sklearn
    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        super().__init__(metadata_key, attr_label)

    def compute(
        self, docs_annotator_1: List[TextDocument], docs_annotator_2: List[TextDocument]
    ) -> Dict:
        ann1_tags_by_attr = self._format_docs_for_evaluation(docs_annotator_1)
        ann2_tags_by_attr = self._format_docs_for_evaluation(docs_annotator_2)

        common_attrs = set(ann1_tags_by_attr.keys()).intersection(
            ann2_tags_by_attr.keys()
        )
        all_scores = {}
        for attr in common_attrs:
            score = cohen_kappa(y1=ann1_tags_by_attr[attr], y2=ann2_tags_by_attr[attr])
            all_scores[attr] = {
                "cohen_kappa": score,
                "ents_support": len(ann1_tags_by_attr[attr]),
            }

        return all_scores


class DocumentAttrKrippendorffAlpha(DocumentAttrMetric):
    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        super().__init__(metadata_key, attr_label)

    def compute(self, docs_annotators: List[List[TextDocument]]) -> Dict:
        if len(docs_annotators) < 2:
            raise ValueError(
                "'docs_annotators' should contain at least two list of TextDocuments to"
                " compare"
            )

        all_annotators_tags_by_attr = defaultdict(list)

        for docs in docs_annotators:
            tags_by_attr = self._format_docs_for_evaluation(docs)

            for attr, tags in tags_by_attr.items():
                all_annotators_tags_by_attr[attr].append(tags)

        all_scores = {}
        for attr in all_annotators_tags_by_attr.keys():
            score = krippendorff_alpha(all_annotators_tags_by_attr[attr])
            all_scores[attr] = {
                "krippendorff_alpha": score,
                "docs_support": len(all_annotators_tags_by_attr[attr][0]),
            }

        return all_scores


class EntityAttrKrippendorffAlpha(EntityAttrMetric):
    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        super().__init__(metadata_key, attr_label)

    def compute(self, docs_annotators: List[List[TextDocument]]) -> Dict:
        if len(docs_annotators) < 2:
            raise ValueError(
                "'docs_annotators' should contain at least two list of TextDocuments to"
                " compare"
            )

        all_annotators_tags_by_attr = defaultdict(list)

        for docs in docs_annotators:
            tags_by_attr = self._format_docs_for_evaluation(docs)

            for attr, tags in tags_by_attr.items():
                all_annotators_tags_by_attr[attr].append(tags)

        all_scores = {}
        for attr in all_annotators_tags_by_attr.keys():
            score = krippendorff_alpha(all_annotators_tags_by_attr[attr])
            all_scores[attr] = {
                "krippendorff_alpha": score,
                "entities_support": len(all_annotators_tags_by_attr[attr][0]),
            }

        return all_scores
