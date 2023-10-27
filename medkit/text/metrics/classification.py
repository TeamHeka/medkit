__all__ = ["TextClassificationEvaluator"]
"""Metrics to assess classification of anns"""
import dataclasses
from typing import Dict, List

from sklearn.metrics import classification_report

from medkit.core.text import TextDocument
from medkit.text.metrics.irr_utils import cohen_kappa, krippendorff_alpha


@dataclasses.dataclass()
class TextClassificationEvaluator:
    """An evaluator for attributes of TextDocuments.

    Attributes
    ----------
    metadata_key:
        Key to sorting each list of documents, it ensures the same order to compute the metric
    attr_label:
        Label of the attribute to evaluate.
    """

    metadata_key: str
    attr_label: str

    def _format_docs_for_evaluation(
        self, docs: List[TextDocument]
    ) -> Dict[str, List[str]]:
        """Format docs attrs to compute the metric

        Parameters
        ----------
        docs : List[TextDocument]
            List of documents with attributes

        Returns
        -------
        attr_values :  List[str]
            List with the str representation of the attribute by document
        """
        # sort documents using the same metadata_key
        docs = sorted(docs, key=lambda x: x.metadata[self.metadata_key])
        attr_values = []
        for doc in docs:
            attrs = doc.attrs.get(label=self.attr_label)

            if not attrs:
                raise ValueError(
                    f"No attribute with label {self.attr_label} was found in the"
                    " document"
                )

            # TBD: attr.to_str() or attr.value, where value is
            # the str representation of the attr
            attr_values.append(attrs[0].to_brat())
        return attr_values

    def compute_classification_repport(
        self,
        true_docs: List[TextDocument],
        predicted_docs: List[TextDocument],
        metrics_by_attr_value: bool = True,
    ) -> Dict[str, float]:
        """Compute classification metrics of document attributes giving annotated documents.
        This method use `sklearn.metrics.classification_report` to compute
        precision, recall and F1-score for value of the attribute.

        Parameters
        ----------
        true_docs:
            Text documents containing attributes of reference
        predicted_docs:
            Text documents containing predicted attributes
        metrics_by_attr_value:
            Whether return metrics by attribute value.
            If False, only overall metrics are returned

        Returns
        -------
        Dict[str,float]:
            A dictionary with the computed metrics
        """
        true_tags = self._format_docs_for_evaluation(true_docs)
        pred_tags = self._format_docs_for_evaluation(predicted_docs)

        report = classification_report(
            y_true=true_tags,
            y_pred=pred_tags,
            output_dict=True,
            zero_division=0,
        )

        # add overall_metrics
        # return 'attr_value'_'metric'
        scores = {f"overall_{key}": value for key, value in report["macro avg"].items()}
        scores["overall_acc"] = report.pop("accuracy")

        if metrics_by_attr_value:
            values_keys = [key for key in report.keys() if not key.endswith("avg")]
            for value_key in values_keys:
                for metric_key, metric_value in report[value_key].items():
                    scores[f"{value_key}_{metric_key}"] = metric_value

        return scores

    def compute_cohen_kappa(
        self, docs_annotator_1: List[TextDocument], docs_annotator_2: List[TextDocument]
    ) -> Dict[str, float]:
        """Compute the cohen's kappa score, an inter-rated agreement score between two annotators.

        .. note::
            See :mod:`medkit.text.metrics.irr_utils.cohen_kappa` for more information about the score

        Parameters
        ----------
        docs_annotator_1:
            Text documents containing attributes annotated by the first annotator
        docs_annotator_2:
            Text documents to compare, these documents contain attributes
            annotated by the other annotator

        Returns
        -------
        Dict[str, float]:
            A dictionary with cohen's kappa score and support
        """
        ann1_tags = self._format_docs_for_evaluation(docs_annotator_1)
        ann2_tags = self._format_docs_for_evaluation(docs_annotator_2)

        scores = {
            "cohen_kappa": cohen_kappa(tags_rater1=ann1_tags, tags_rater2=ann2_tags),
            "support": len(ann1_tags),
        }

        return scores

    def compute_krippendorff_alpha(
        self, docs_annotators: List[List[TextDocument]]
    ) -> Dict[str, float]:
        """Compute the Krippendorff alpha score, an inter-rated agreement score between
        multiple annotators.

        .. note::
            See :mod:`medkit.text.metrics.irr_utils.krippendorff_alpha` for more information about the score

        Parameters
        ----------
        docs_annotators:
            A list of Text documents containing attributes.
            The size of the list is the number of annotators to compare.

        Returns
        -------
        Dict[str, float]:
            A dictionary with the krippendorff alpha score and support.
        """
        if len(docs_annotators) < 2:
            raise ValueError(
                "'docs_annotators' should contain at least two list of TextDocuments to"
                " compare"
            )

        all_annotators_data = []

        for docs in docs_annotators:
            annotator_tags = self._format_docs_for_evaluation(docs)
            all_annotators_data.append(annotator_tags)
        scores = {
            "krippendorff_alpha": krippendorff_alpha(all_annotators_data),
            "support": len(all_annotators_data[0]),
        }

        return scores
