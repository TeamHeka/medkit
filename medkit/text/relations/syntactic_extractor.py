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
    output_label = "SYNTACTIC_REL"


class SyntacticRelationExtractor:
    """Extractor of syntactic relations between entities in a document.
    The relation relies on the dependency parser from a spacy pipeline.

    To obtain consistent results, the spacy model should have the
    same language as the documents in which relations should be found."""

    def __init__(
        self,
        name_spacy_model: Union[str, Path] = DefaultConfig.name_spacy_model,
        output_label: str = DefaultConfig.output_label,
        label_entities: Optional[List[str]] = None,
        proc_id: Optional[str] = None,
    ):
        if proc_id is None:
            proc_id = generate_id()

        self.id = proc_id
        self._prov_builder: Optional[ProvBuilder] = None
        self.label_entities = label_entities
        self.output_label = output_label

        try:
            self.nlp = spacy.load(
                name_spacy_model, exclude=["tagger", "ner", "lemmatizer"]
            )
            self.name_spacy_model = name_spacy_model
        except OSError:
            msg = (
                "Model for language was not found. Please "
                'run "python -m spacy download {}" before running this annotator '
            ).format(name_spacy_model)
            raise OSError(msg)

    @property
    def description(self) -> OperationDescription:
        config = dict(
            name_spacy_model=self.name_spacy_model,
            label_entities=self.label_entities,
            output_label=self.output_label,
        )
        return OperationDescription(
            id=self.id, name=self.__class__.__name__, config=config
        )

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

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
            print(f"{len(relations)} syntactic relations were found")

            # TBD: this operation should be add relations in the document ?
            for rel in relations:
                medkit_doc.add_annotation(rel)

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
        spacy_doc = self._merge_entities(spacy_doc)

        relations = []
        for sentence in spacy_doc.sents:
            ents = sentence.ents
            # find a binary relation between e1 and e2
            for idx, e1 in enumerate(ents[:-1]):
                e2 = ents[idx + 1]
                right_child_tokens_of_e1 = [token.i for token in e1.rights]
                left_child_tokens_of_e2 = [token.i for token in e2.lefts]

                if e2.start in right_child_tokens_of_e1:
                    # a relation left to right exist
                    # e1 is the head of the relation
                    relation = self._create_relation(
                        head=e1,
                        target=e2,
                        metadata=dict(dep_tag=e2.root.dep_, dependency="left_to_right"),
                    )
                    relations.append(relation)

                elif e1.start in left_child_tokens_of_e2:
                    # a relation right to left exist
                    # e2 is the head of the relation
                    relation = self._create_relation(
                        head=e2,
                        target=e1,
                        metadata=dict(dep_tag=e1.root.dep_, dependency="right_to_left"),
                    )

                    relations.append(relation)

        return relations

    def _create_relation(
        self, head: SpacySpan, target: SpacySpan, metadata: Dict[str, str]
    ) -> Relation:
        """
        Parse the spacy relation content into a Relation object.

        Parameters
        ----------
        head:
            Spacy entity head of the syntactic relation
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
            relation = Relation(
                label=self.output_label,
                source_id=head._.get(spacy_utils._ATTR_MEDKIT_ID),
                target_id=target._.get(spacy_utils._ATTR_MEDKIT_ID),
                metadata=metadata,
            )

            # set provenance
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    # TODO:
                    # in terms of provenance which is the source data item ?
                    relation,
                    self.description,
                    source_data_items=[],
                )

            return relation

        except Exception as err:
            raise ValueError(f"Impossible to parse the relation. Reason : {err}")

    def _merge_entities(self, spacy_doc: Doc) -> Doc:
        """Merge entities into a single token"""
        with spacy_doc.retokenize() as retokenizer:
            for ent in spacy_doc.ents:
                retokenizer.merge(ent)
        return spacy_doc
