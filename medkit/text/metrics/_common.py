import abc
from typing import Dict, List, Optional
from medkit.core.text import span_utils

from medkit.core.text.document import TextDocument


class DocumentAttrMetric:
    """A base class to defining metrics that evaluate the attributes value of TextDocuments.
    The 'compute' method must be implemented for each metric. For each attribute, its `str`
    version is used to generate a tag.
    """

    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        self.attr_label = attr_label
        self.metadata_key = metadata_key

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
        data :  Dict[str,List[str]]
            Dictionnary with attributes found in the list of the documents.
        """
        # sort documents using the same metadata_key
        docs = sorted(docs, key=lambda x: x.metadata[self.metadata_key])
        data = {}
        for doc in docs:
            for attr in doc.attrs.get(label=self.attr_label):
                if attr.label not in data:
                    data[attr.label] = []
                # TBD: to_str
                data[attr.label].append(attr.to_brat())
        return data

    @abc.abstractmethod
    def compute(self, **kwargs) -> Dict:
        raise NotImplementedError


class EntityAttrMetric:
    """A base class to defining metrics that evaluate the attributes value of Entities by document.
    The 'compute' method must be implemented for each metric. For each attribute, its `str`
    version is used to generate a tag.
    """

    def __init__(self, metadata_key, attr_label: Optional[str] = None):
        self.attr_label = attr_label
        self.metadata_key = metadata_key

    def _format_docs_for_evaluation(
        self, docs: List[TextDocument]
    ) -> Dict[str, List[str]]:
        """Format entities attrs by doc to compute the metric

        Parameters
        ----------
        docs : List[TextDocument]
            List of documents with attributes in entities

        Returns
        -------
        data :  Dict[str,List[str]]
            Dictionnary with attributes found in the entitites
            from the list of the documents.
        """
        # sort documents using the same metadata_key
        docs = sorted(docs, key=lambda x: x.metadata[self.metadata_key])
        data = {}
        for doc in docs:
            sorted_ents = sorted(
                [
                    ent
                    for ent in doc.anns.get_entities()
                    if span_utils.normalize_spans(ent.spans)
                ],
                key=lambda e: e.spans[0].start,
            )

            for ent in sorted_ents:
                for attr in ent.attrs.get(label=self.attr_label):
                    if attr.label not in data:
                        data[attr.label] = []
                    # TBD: to str
                    data[attr.label].append(attr.to_brat())
        return data

    @abc.abstractmethod
    def compute(self, **kwargs) -> Dict:
        raise NotImplementedError
