"""Metrics to assess classification of anns"""
from typing import Dict, List, Optional
from sklearn.metrics import classification_report

from medkit.core.text import TextDocument
from medkit.text.metrics._common import DocumentAttrMetric, EntityAttrMetric


class DocumentAttrClassificationReport(DocumentAttrMetric):
    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        super().__init__(metadata_key, attr_label)

    def compute(
        self, true_docs: List[TextDocument], predicted_docs: List[TextDocument]
    ) -> Dict:
        true_tags_by_attr = self._format_docs_for_evaluation(true_docs)
        pred_tags_by_attr = self._format_docs_for_evaluation(predicted_docs)

        common_attrs = set(true_tags_by_attr.keys()).intersection(
            pred_tags_by_attr.keys()
        )
        all_scores = {}
        for attr in common_attrs:
            scores = classification_report(
                y_true=true_tags_by_attr[attr],
                y_pred=pred_tags_by_attr[attr],
                output_dict=True,
                zero_division=0,
            )
            all_scores[attr] = scores

        return all_scores


class EntityAttrClassificationReport(EntityAttrMetric):
    # backend sklearn
    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        super().__init__(metadata_key, attr_label)

    def compute(
        self, true_docs: List[TextDocument], predicted_docs: List[TextDocument]
    ) -> Dict:
        true_tags_by_attr = self._format_docs_for_evaluation(true_docs)
        pred_tags_by_attr = self._format_docs_for_evaluation(predicted_docs)

        common_attrs = set(true_tags_by_attr.keys()).intersection(
            pred_tags_by_attr.keys()
        )
        all_scores = {}
        for attr in common_attrs:
            scores = classification_report(
                y_true=true_tags_by_attr[attr],
                y_pred=pred_tags_by_attr[attr],
                output_dict=True,
                zero_division=0,
            )
            all_scores[attr] = scores

        return all_scores
