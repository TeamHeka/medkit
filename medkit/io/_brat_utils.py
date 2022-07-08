import dataclasses
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from smart_open import open
from medkit.core.text.annotation import Segment, Relation
from medkit.core import Attribute

from medkit.core.text.span_utils import normalize_spans

GROUPING_ENTITIES = frozenset(["And-Group", "Or-Group"])
GROUPING_RELATIONS = frozenset(["And", "Or"])


@dataclass
class BratEntity:
    """A simple entity annotation data structure."""

    id: str
    type: str
    span: Tuple[Tuple[int, int], ...]
    text: str

    @property
    def start(self) -> int:
        return self.span[0][0]

    @property
    def end(self) -> int:
        return self.span[-1][-1]

    def to_str(self) -> str:
        spans_str = ";".join(f"{span[0]} {span[1]}" for span in self.span)
        return f"{self.id}\t{self.type} {spans_str}\t{self.text}\n"


@dataclass
class BratRelation:
    """A simple relation data structure."""

    id: str
    type: str
    subj: str
    obj: str

    def to_str(self) -> str:
        return f"{self.id}\t{self.type} Arg1:{self.subj} Arg2:{self.obj}\n"


@dataclass
class BratAttribute:
    """A simple attribute data structure."""

    id: str
    type: str
    target: str
    value: str = None  # Only one value is possible

    def to_str(self) -> str:
        value = "" if self.value is None else f" {self.value}"
        return f"{self.id}\t{self.type} {self.target}{value}\n"


@dataclass
class Grouping:
    """A grouping data structure for entities  of type 'And-Group", "Or-Group'"""

    id: str
    type: str
    items: List[BratEntity]

    @property
    def text(self):
        return f" {self.type.split('-')[0]} ".join(i.text for i in self.items)


@dataclass
class BratAugmentedEntity:
    """An augmented entity data structure with its relations and attributes."""

    id: str
    type: str
    span: Tuple[Tuple[int, int], ...]
    text: str
    relations_from_me: Tuple[BratRelation, ...]
    relations_to_me: Tuple[BratRelation, ...]
    attributes: Tuple[BratAttribute, ...]

    @property
    def start(self) -> int:
        return self.span[0][0]

    @property
    def end(self) -> int:
        return self.span[-1][-1]


@dataclass
class BratDocument:
    entities: Dict[str, BratEntity]
    relations: Dict[str, BratRelation]
    attributes: Dict[str, BratAttribute]
    groups: Dict[str, Grouping] = None

    def get_augmented_entities(self) -> Dict[str, BratAugmentedEntity]:
        augmented_entities = {}
        for entity in self.entities.values():
            entity_relations_from_me = []
            entity_relations_to_me = []
            entity_attributes = []
            for relation in self.relations.values():
                if relation.subj == entity.id:
                    entity_relations_from_me.append(relation)
                if relation.obj == entity.id:
                    entity_relations_to_me.append(relation)
            for attribute in self.attributes.values():
                if attribute.target == entity.id:
                    entity_attributes.append(attribute)
            augmented_entities[entity.id] = BratAugmentedEntity(
                id=entity.id,
                type=entity.type,
                span=entity.span,
                text=entity.text,
                relations_from_me=tuple(entity_relations_from_me),
                relations_to_me=tuple(entity_relations_to_me),
                attributes=tuple(entity_attributes),
            )
        return augmented_entities


# data structures for configuration
@dataclass
class RelationConf:
    """Configuration data structure of a BratRelation"""

    type: str
    args1: Set[str] = dataclasses.field(default_factory=set)
    args2: Set[str] = dataclasses.field(default_factory=set)

    def to_str(self) -> str:
        arg1 = "|".join([str(arg) for arg in self.args1])
        arg2 = "|".join([str(arg) for arg in self.args2])
        return f"{self.type}\tArg1:{arg1}, Arg2:{arg2}"

    def update(self, args1: Set[str], args2: Set[str]):
        self.args1.update(args1)
        self.args2.update(args2)


@dataclass
class AttributeConf:
    """Configuration data structure of a BratAttribure"""

    from_entity: bool
    type: str
    values: Set[str] = dataclasses.field(default_factory=set)

    def to_str(self) -> str:
        arg = "<ENTITY>" if self.from_entity else "<RELATION>"
        values_str = "|".join([str(value) for value in self.values])
        return (
            f"{self.type}\tArg:{arg}"
            if not values_str
            else f"{self.type}\tArg:{arg}, Value:{values_str}"
        )

    def update(self, values: Set[str]):
        self.values.update(values)


@dataclass
class BratAnnConfiguration:
    """A data structure to represent 'annotation.conf' in brat documents.
    This is necessary to generate a valid annotation project in brat.
    An 'annotation.conf' has four sections. The section 'events' is not
    supported in medkit, so the section is empty.
    """

    entity_types: Set[str]
    relation_types: Dict[str, RelationConf]  # key: relation type
    attribute_types: Dict[str, AttributeConf]  # key: attribute_type

    def add_relation_type(self, relation: RelationConf):
        if relation.type not in self.relation_types:
            self.relation_types[relation.type] = relation
        else:
            self.relation_types[relation.type].update(relation.args1, relation.args2)

    def add_attribute_type(self, attribute: AttributeConf):
        if attribute.type not in self.attribute_types:
            self.attribute_types[attribute.type] = attribute
        else:
            self.attribute_types[attribute.type].update(attribute.values)

    def add_entity_types(self, entity_types: Set[str]):
        self.entity_types.update(entity_types)

    def to_str(self) -> str:
        annotation_conf = (
            "#Text-based definitions of entity types, relation types\n"
            "#and attributes. This file was generated using medkit\n"
            "#from the HeKa project"
        )
        annotation_conf += "\n[entities]\n\n"
        entity_section = "\n".join([ent for ent in self.entity_types])
        annotation_conf += entity_section

        annotation_conf += "\n[relations]\n\n"
        annotation_conf += "# This line enables entity overlapping\n"
        annotation_conf += "<OVERLAP>\tArg1:<ENTITY>, Arg2:<ENTITY>, <OVL-TYPE>:<ANY>\n"
        relation_section = "\n".join(
            relation.to_str() for relation in self.relation_types.values()
        )
        annotation_conf += relation_section

        annotation_conf += "\n[attributes]\n\n"
        attribute_section = "\n".join(
            attribute.to_str() for attribute in self.attribute_types.values()
        )
        annotation_conf += attribute_section

        annotation_conf += "\n[events]\n\n"
        return annotation_conf


def parse_file(ann_path: Union[str, Path], detect_groups: bool = False) -> BratDocument:
    """
    Read an annotation file to get the Entities, Relations and Attributes in it.
    All other lines are ignored.

    Parameters
    ----------
    ann_path: str
        The path to the annotation file to be processed.
    detect_groups: bool, optional
        If set to `True`, the function will also parse the group of entities according
        to some specific keywords.
        By default, it is set to False.

    Returns
    -------
    Document
        The dataclass object containing entities, relations and attributes

    """
    with open(ann_path, encoding="utf-8") as ann_file:
        ann_content = ann_file.read()
    document = parse_string(ann_content, detect_groups)
    return document


def parse_string(ann_string: str, detect_groups: bool = False) -> BratDocument:
    """
    Read a string containing all annotations and extract Entities, Relations and
    Attributes.
    All other lines are ignored.

    Parameters
    ----------
    ann_string: str
        The string containing all brat annotations
    detect_groups: bool, optional
        If set to `True`, the function will also parse the group of entities according
        to some specific keywords.
        By default, it is set to False.

    Returns
    -------
    Document
        The dataclass object containing entities, relations and attributes
    """
    entities = dict()
    relations = dict()
    attributes = dict()

    annotations = ann_string.split("\n")
    for i, ann in enumerate(annotations):
        line_number = i + 1
        if len(ann) == 0 or ann[0] not in ("T", "R", "A"):
            logging.info(
                "Ignoring empty line or unsupported annotation %s on line %d",
                ann,
                line_number,
            )
            continue
        ann_id, ann_content = ann.split("\t", maxsplit=1)
        try:
            if ann.startswith("T"):
                entity = _parse_entity(ann_id, ann_content)
                entities[entity.id] = entity
            elif ann.startswith("R"):
                relation = _parse_relation(ann_id, ann_content)
                relations[relation.id] = relation
            elif ann.startswith("A"):
                attribute = _parse_attribute(ann_id, ann_content)
                attributes[attribute.id] = attribute
        except ValueError as err:
            logging.info(err)
            logging.info(f"Ignore annotation {ann_id} at line {line_number}")

    # Process groups
    groups = None
    if detect_groups:
        groups: Dict[str, Grouping] = dict()
        grouping_relations = {
            r.id: r for r in relations.values() if r.type in GROUPING_RELATIONS
        }

        for entity in entities.values():
            if entity.type in GROUPING_ENTITIES:
                items: List[BratEntity] = list()
                for relation in grouping_relations.values():
                    if relation.subj == entity.id:
                        items.append(entities[relation.obj])
                groups[entity.id] = Grouping(entity.id, entity.type, items)

    return BratDocument(entities, relations, attributes, groups)


def _parse_entity(entity_id: str, entity_content: str) -> BratEntity:
    """
    Parse the brat entity string into an Entity structure.

    Parameters
    ----------
    entity_id: str
        The ID defined in the brat annotation (e.g.,`T12`)
    entity_content: str
        The string content for this ID to parse
         (e.g., `Temporal-Modifier 116 126\thistory of`)

    Returns
    -------
    BratEntity
        The dataclass object representing the entity

    Raises
    ------
    ValueError
        Raises when the entity can't be parsed
    """
    try:
        tag_and_spans, text = entity_content.strip().split("\t", maxsplit=1)
        text = text.replace("\t", " ")  # Remove tabs in text

        tag, spans_text = tag_and_spans.split(" ", maxsplit=1)
        span_list = spans_text.split(";")
        spans: List[Tuple[int, int]] = []
        for span in span_list:
            start_s, end_s = span.split()
            start, end = int(start_s), int(end_s)
            spans.append((start, end))
        return BratEntity(entity_id.strip(), tag.strip(), tuple(spans), text.strip())
    except Exception as err:
        raise ValueError("Impossible to parse entity. Reason : %s" % err)


def _parse_relation(relation_id: str, relation_content: str) -> BratRelation:
    """
    Parse the annotation string into a Relation structure.

    Parameters
    ----------
    relation_id: str
        The ID defined in the brat annotation (e.g., R12)
    relation_content: str
        The relation text content. (e.g., `Modified-By Arg1:T8 Arg2:T6\t`)

    Returns
    -------
    BratRelation
        The dataclass object representing the relation

    Raises
    ------
    ValueError
        Raises when the relation can't be parsed
    """

    try:
        relation, subj, obj = relation_content.strip().split()
        subj = subj.replace("Arg1:", "")
        obj = obj.replace("Arg2:", "")
        return BratRelation(
            relation_id.strip(), relation.strip(), subj.strip(), obj.strip()
        )
    except Exception as err:
        raise ValueError("Impossible to parse the relation. Reason : %s" % err)


def _parse_attribute(attribute_id: str, attribute_content: str) -> BratAttribute:
    """
    Parse the annotation string into an Attribute structure.

    Parameters
    ----------
    attribute_id : str
        The attribute ID defined in the annotation. (e.g., `A1`)
    attribute_content: str
         The attribute text content. (e.g., `Tense T19 Past-Ended`)

    Returns
    -------
    BratAttribute:
        The dataclass object representing the attribute

    Raises
    ------
    ValueError
        Raises when the attribute can't be parsed
    """

    attribute_arguments = attribute_content.strip().split(" ", maxsplit=2)
    if len(attribute_arguments) < 2:
        raise ValueError("Impossible to parse the input attribute")

    attribute_name = attribute_arguments[0]
    attribute_target = attribute_arguments[1]
    attribute_value = None

    if len(attribute_arguments) > 2:
        attribute_value = attribute_arguments[2].strip()

    return BratAttribute(
        attribute_id.strip(),
        attribute_name.strip(),
        attribute_target.strip(),
        attribute_value,
    )


def _convert_segment_to_brat(segment: Segment, nb_segment: int) -> BratEntity:
    """
    Get a brat entity from a medkit segment

    Parameters
    ----------
    segment:
        A medkit segment to convert into brat format
    nb_segment:
        The current counter of brat segments

    Returns
    -------
    BratEntity
        The equivalent brat entity of the medkit segment
    """
    assert nb_segment != 0
    brat_id = f"T{nb_segment}"
    # brat does not support spaces in labels
    type = segment.label.replace(" ", "_")
    text = segment.text
    spans = tuple((span.start, span.end) for span in normalize_spans(segment.spans))
    return BratEntity(brat_id, type, spans, text)


def _convert_relation_to_brat(
    relation: Relation,
    nb_relation: int,
    brat_anns_by_segment_id: Dict[str, BratEntity],
) -> Tuple[BratRelation, RelationConf]:
    """
    Get a brat relation from a medkit relation

    Parameters
    ----------
    relation:
        A medkit relation to convert into brat format
    nb_relation:
        The current counter of brat relations
    brat_anns_by_segment_id:
        A dict to map medkit ID to brat annotation

    Returns
    -------
    BratRelation
        The equivalent brat relation of the medkit relation
    RelationConf
        Configuration of the brat attribute

    """
    assert nb_relation != 0
    brat_id = f"R{nb_relation}"
    # brat does not support spaces in labels
    type = relation.label.replace(" ", "_")
    subj = brat_anns_by_segment_id.get(relation.source_id)
    obj = brat_anns_by_segment_id.get(relation.target_id)

    if subj is None or obj is None:
        raise ValueError(
            "Imposible to create brat relation, entity target/source was not found."
        )

    relation_conf = RelationConf(
        type=type, args1=set([subj.type]), args2=set([obj.type])
    )

    return BratRelation(brat_id, type, subj.id, obj.id), relation_conf


def _convert_attribute_to_brat(
    attribute: Attribute, nb_attribute: int, target_brat_id: str, is_from_entity: bool
) -> BratAttribute:
    """
    Get a brat attribute from a medkit attribute

    Parameters
    ----------
    attribute:
        A medkit attribute to convert into brat format
    nb_attribute:
        The current counter of brat attributes
    target_brat_id:
        Corresponding target brat ID
    is_from_entity:
        Whether `atrribute` comes from an entity

    Returns
    -------
    BratAttribute:
        The equivalent brat attribute of the medkit attribute
    AttributeConf:
        Configuration of the brat attribute
    """
    assert nb_attribute != 0
    brat_id = f"A{nb_attribute}"
    type = attribute.label.replace(" ", "_")
    value = attribute.value

    values = set() if value is None else set([value])
    attr_conf = AttributeConf(from_entity=is_from_entity, type=type, values=values)

    return BratAttribute(brat_id, type, target_brat_id, value), attr_conf
