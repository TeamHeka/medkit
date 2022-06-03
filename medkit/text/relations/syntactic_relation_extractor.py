__all__ = ["SyntacticRelationExtractor"]
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import spacy
from spacy.tokens import Doc
from spacy.tokens import Span as SpacySpan

from medkit.core import OperationDescription, ProvBuilder, generate_id
from medkit.core.text import Relation, TextDocument
from medkit.text.spacy import spacy_utils


@dataclass
class DefaultConfig:
    name_spacy_model = "fr_core_news_sm"
    relation_label = "has_syntactic_rel"
    include_right_to_left_relations = True


class SyntacticRelationExtractor:
    """Extractor of syntactic relations between entities in a document.
    The relation relies on the dependency parser from a spacy pipeline"""

    def __init__(
        self,
        name_spacy_model: Union[str, Path] = DefaultConfig.name_spacy_model,
        relation_label: str = DefaultConfig.relation_label,
        label_entities: Optional[List[str]] = None,
        include_right_to_left_relations: bool = DefaultConfig.include_right_to_left_relations,
        proc_id: Optional[str] = None,
    ):
        """Initialize the syntactic relation extractor

        Parameters
        ----------
        name_spacy_model: str
            Name or path of a spacy pipeline to load, it should be include a
            syntactic dependency parser. To obtain consistent results,
            the spacy model should have the same language as the documents
            in which relations should be found.
        relation_label: str
            Label of identified relations
        label_entities: str
            Labels of medkit annotations on which relations are to be identified.
            If `None` (default) relations are identified in all entities of a TextDocument
        include_right_to_left_relations:
            Include relations that begin at the right-most entity. Since the reading
            direction is generally from left to right, 'right-to-left' relations
            may be less accurate depending on the use case.
        proc_id:
            Identifier of the relation extractor
        """

        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self._prov_builder: Optional[ProvBuilder] = None
        self.label_entities = label_entities
        self.relation_label = relation_label
        self.nlp = self._load_model_spacy(name_spacy_model)
        self.name_spacy_model = name_spacy_model
        self.include_right_to_left_relations = include_right_to_left_relations

    @property
    def description(self) -> OperationDescription:
        config = dict(
            name_spacy_model=self.name_spacy_model,
            label_entities=self.label_entities,
            relation_label=self.relation_label,
            include_right_to_left_relations=self.include_right_to_left_relations,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def _load_model_spacy(self, name_spacy_model: str):
        try:
            nlp = spacy.load(name_spacy_model, exclude=["tagger", "ner", "lemmatizer"])
            return nlp
        except OSError:
            msg = (
                "Model for language was not found. Please "
                'run "python -m spacy download {}" before running this annotator '
            ).format(name_spacy_model)
            raise OSError(msg)

    def run(self, documents: List[TextDocument]):

        for medkit_doc in documents:
            # build spacy doc
            spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
                nlp=self.nlp,
                medkit_doc=medkit_doc,
                labels_anns=self.label_entities,
                attrs=[],
                include_medkit_info=True,
            )
            # apply nlp spacy to include dependence tag
            spacy_doc = self.nlp(spacy_doc)
            relations = self._find_syntactic_relations(spacy_doc)
            self._add_relations_to_document(medkit_doc, relations)

    def _find_syntactic_relations(self, spacy_doc: Doc):
        """
        Find syntactic relations from entities present in the same sentence.
        For each dependance found, a new relation is created.

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

        # spacy doc has not been parsed
        if not spacy_doc.has_annotation("DEP"):
            return relations

        for sentence in spacy_doc.sents:
            ents = sentence.ents
            # find a binary relation between e1 and e2
            for idx, e1 in enumerate(ents[:-1]):
                e2 = ents[idx + 1]
                right_child_tokens_of_e1 = [token.i for token in e1.rights]
                left_child_tokens_of_e2 = [token.i for token in e2.lefts]

                if any(token.i in right_child_tokens_of_e1 for token in e2):
                    # a relation left to right exist, e1 is the source of the relation
                    relation = self._create_relation(
                        source=e1,
                        target=e2,
                        metadata=dict(dep_tag=e2.root.dep_, dependency="left_to_right"),
                    )
                    relations.append(relation)

                elif (
                    any(token.i in left_child_tokens_of_e2 for token in e1)
                    and self.include_right_to_left_relations
                ):
                    # a relation right to left exist, e2 is the source of the relation
                    relation = self._create_relation(
                        source=e2,
                        target=e1,
                        metadata=dict(dep_tag=e1.root.dep_, dependency="right_to_left"),
                    )

                    relations.append(relation)

        return relations

    def _create_relation(
        self, source: SpacySpan, target: SpacySpan, metadata: Dict[str, str]
    ) -> Relation:
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
        Relation
            The Relation object representing the spacy relation

        Raises
        ------
        ValueError
            Raises when the relation can't be parsed
        """

        try:
            attribute_medkit_id = spacy_utils._ATTR_MEDKIT_ID
            source_id = source._.get(attribute_medkit_id)
            target_id = target._.get(attribute_medkit_id)

            if source_id is None or target_id is None:
                raise RuntimeError(
                    f"The attribute {attribute_medkit_id} was not transferred to spacy"
                )

            relation = Relation(
                source_id=source_id,
                target_id=target_id,
                label=self.relation_label,
                metadata=metadata,
            )
            return relation

        except Exception as err:
            raise ValueError(f"Impossible to parse the relation. Reason : {err}")

    def _add_relations_to_document(
        self, medkit_doc: TextDocument, relations: List[Relation]
    ):
        for relation in relations:
            medkit_doc.add_annotation(relation)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    relation, self.description, source_data_items=[]
                )

        if relations:
            print(f"{len(relations)} syntactic relations were added in the document")
