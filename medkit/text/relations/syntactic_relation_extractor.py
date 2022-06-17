__all__ = ["SyntacticRelationExtractor"]
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import spacy
from spacy.tokens import Doc, Span as SpacySpan

from medkit.core import OperationDescription, ProvBuilder, generate_id
from medkit.core.text import Relation, TextDocument
from medkit.text.spacy import spacy_utils

logger = logging.getLogger(__name__)


@dataclass
class DefaultConfig:
    name_spacy_model = "fr_core_news_sm"
    relation_label = "has_syntactic_rel"
    include_right_to_left_relations = True


class SyntacticRelationExtractor:
    """Extractor of syntactic relations between entities in a TextDocument.
    The relation relies on the dependency parser from a spacy pipeline.

    A transition-based dependency parser defines a dependency tag for each
    token (word) in a document. This relation extractor uses syntactic neighbours
    of the words of an entity to determine whether a dependency exists
    between the entities.

    Each TextDocument is converted to a spacy doc with the selected entities.
    By default, all entities are transferred and the source and target of the relations
    depends on the syntactic dependency.
    """

    def __init__(
        self,
        name_spacy_model: Union[str, Path] = DefaultConfig.name_spacy_model,
        relation_label: str = DefaultConfig.relation_label,
        entities_labels: Optional[List[str]] = None,
        entities_source: Optional[List[str]] = None,
        entities_target: Optional[List[str]] = None,
        include_right_to_left_relations: bool = DefaultConfig.include_right_to_left_relations,
        proc_id: Optional[str] = None,
    ):
        """Initialize the syntactic relation extractor

        Parameters
        ----------
        name_spacy_model: str
            Name or path of a spacy pipeline to load, it should include a
            syntactic dependency parser. To obtain consistent results,
            the spacy model should have the same language as the documents
            in which relations should be found.
        relation_label: str
            Label of identified relations
        entities_labels: Optional[List[str]]
            Labels of medkit entities on which relations are to be identified.
            If `None` (default) relations are identified in all entities of a TextDocument
        entities_source: List[str]
            Labels of medkit entities defined as source of the relation.
            If `None` (default) the source is the syntactic source.
        entities_target: List[str]
            Labels of medkit entities defined as target of the relation.
            If `None` (default) the target is the syntactic target.
        include_right_to_left_relations:
            Include relations that begin at the right-most entity. Since the reading
            direction is generally from left to right, 'right-to-left' relations
            may be less accurate depending on the use case.
        proc_id:
            Identifier of the relation extractor

        Raises
        ------
        ValueError
            If the spacy model defined by `name_spacy_model` does not parse a document
        """

        if proc_id is None:
            proc_id = generate_id()
        if entities_source is None:
            entities_source = []
        if entities_target is None:
            entities_target = []

        self.id = proc_id
        self._prov_builder: Optional[ProvBuilder] = None
        self.relation_label = relation_label
        self.include_right_to_left_relations = include_right_to_left_relations
        self.entities_source = entities_source
        self.entities_target = entities_target

        nlp = spacy.load(name_spacy_model, exclude=["tagger", "ner", "lemmatizer"])
        if not nlp("X").has_annotation("DEP"):
            raise ValueError(
                f"Model `{name_spacy_model}` does not add syntax attributes"
                " to documents and cannot be use with SyntacticRelationExtractor."
            )
        self._nlp = nlp
        self.name_spacy_model = name_spacy_model
        self.entities_labels = entities_labels

    @property
    def description(self) -> OperationDescription:
        config = dict(
            name_spacy_model=self.name_spacy_model,
            entities_source=self.entities_source,
            entities_labels=self.entities_labels,
            entities_target=self.entities_target,
            relation_label=self.relation_label,
            include_right_to_left_relations=self.include_right_to_left_relations,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def run(self, documents: List[TextDocument]):
        """Add relations to each document from `documents`

        Parameters
        ----------
        documents:
            List of text documents in which relations are to be found

        """
        for medkit_doc in documents:
            # build spacy doc using selected entities
            spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
                nlp=self._nlp,
                medkit_doc=medkit_doc,
                labels_anns=self.entities_labels,
                attrs=[],
                include_medkit_info=True,
            )
            # apply nlp spacy to include dependency tag
            spacy_doc = self._nlp(spacy_doc)
            relations = self._find_syntactic_relations(spacy_doc)
            self._add_relations_to_document(medkit_doc, relations)

    def _find_syntactic_relations(self, spacy_doc: Doc):
        """Find syntactic relations from entities present in the same sentence.
        For each dependency found, a new relation is created.

        Parameters
        ----------
        spacy_doc:
            A spacy doc with medkit entities converted in spacy entities

        Returns
        -------
        Relation
            The Relation object representing the spacy relation
        """
        relations = []
        for sentence in spacy_doc.sents:
            ents = sentence.ents
            # find a binary relation between e1 and e2
            for idx, e1 in enumerate(ents[:-1]):
                e2 = ents[idx + 1]
                right_child_tokens_of_e1 = [token.i for token in e1.rights]
                if any(token.i in right_child_tokens_of_e1 for token in e2):
                    # a relation left to right exist, e1 is the syntactic source
                    # of the relation, check if source or target is predefined
                    source, target = self._define_source_target(e1, e2)
                    relation = self._create_relation(
                        source=source,
                        target=target,
                        metadata=dict(
                            dep_tag=e2.root.dep_, dep_direction="left_to_right"
                        ),
                    )
                    if relation is not None:
                        relations.append(relation)

                if self.include_right_to_left_relations:
                    left_child_tokens_of_e2 = [token.i for token in e2.lefts]
                    if any(token.i in left_child_tokens_of_e2 for token in e1):
                        # a relation right to left exist, e2 is the syntactic source
                        # of the relation, check if source or target is predefined
                        source, target = self._define_source_target(e2, e1)
                        relation = self._create_relation(
                            source=source,
                            target=target,
                            metadata=dict(
                                dep_tag=e1.root.dep_, dep_direction="right_to_left"
                            ),
                        )
                        if relation is not None:
                            relations.append(relation)

        return relations

    def _define_source_target(self, source: SpacySpan, target: SpacySpan):
        # change whether origin or target is predefined by the user
        if (
            source.label_ in self.entities_target
            or target.label_ in self.entities_source
        ):
            return target, source
        return source, target

    def _create_relation(
        self, source: SpacySpan, target: SpacySpan, metadata: Dict[str, str]
    ) -> Optional[Relation]:
        """
        Parse the spacy relation content into a Relation object.

        Parameters
        ----------
        source:
            Spacy entity source of the syntactic relation
        target:
            Spacy entity target of the syntactic relation
        metadata:
            Additional information of the relation

        Returns
        -------
        Optional[Relation]
            The Relation object representing the spacy relation

        """

        attribute_medkit_id = spacy_utils._ATTR_MEDKIT_ID
        source_id = source._.get(attribute_medkit_id)
        target_id = target._.get(attribute_medkit_id)

        if source_id is None or target_id is None:
            logging.warning(
                f"Can't create a medkit Relation between `{source.text}` and"
                f" `{target.text}`. Source or target entity has not been detected by"
                " medkit but spacy pipeline, and it is not supported by this module."
            )
            return None

        relation = Relation(
            source_id=source_id,
            target_id=target_id,
            label=self.relation_label,
            metadata=metadata,
        )
        return relation

    def _add_relations_to_document(
        self, medkit_doc: TextDocument, relations: List[Relation]
    ):
        for relation in relations:
            medkit_doc.add_annotation(relation)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    relation,
                    self.description,
                    source_data_items=[medkit_doc.raw_segment],
                )

        if relations:
            logging.info(
                f"{len(relations)} syntactic relations were added in the document"
            )
