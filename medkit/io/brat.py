import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Text, Tuple

from smart_open import open

GROUPING_ENTITIES = frozenset(["And-Group", "Or-Group"])
GROUPING_RELATIONS = frozenset(["And", "Or"])


def remove_empty(iterable: Sequence[Text]) -> Sequence[Text]:
    """
    Returns only non-empty strings from an iterable.

    Parameters
    ==========

    - iterable : Iterable
      An iterable of strings that possibly contains empty strings.

    Returns
    =======
    - The same iterable with the empty strings removed.
    """
    return list(filter(lambda x: len(x.strip()) > 0, iterable))


def sanitize_tabs(line: str, max_tabs: int = 2) -> str:
    sanitized_line: List[str] = []
    tab_count = 0

    for char in line:
        if char == "\t" and tab_count < max_tabs:
            sanitized_line.append(char)
            tab_count += 1
        elif char == "\t" and tab_count == max_tabs:
            sanitized_line.append(" ")
        else:
            sanitized_line.append(char)

    line = "".join(sanitized_line)
    return line


@dataclass
class Entity(object):
    """A simple annotation data structure."""

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


@dataclass
class Relation(object):
    """A simple relation data structure."""

    id: str
    type: str
    subj: str
    obj: str


@dataclass
class Attribute(object):
    """A simple attribute data structure."""

    id: str
    type: str
    target: str
    values: Tuple[str, ...] = tuple()


@dataclass
class Grouping(object):
    id: str
    type: str
    items: List[Entity]

    @property
    def text(self):
        return f" {self.type.split('-')[0]} ".join(i.text for i in self.items)


@dataclass
class AugmentedEntity(object):
    """An augmented entity data structure with its relations and attributes."""

    id: str
    type: str
    span: Tuple[Tuple[int, int], ...]
    text: str
    relations_from_me: Tuple[Relation, ...]
    relations_to_me: Tuple[Relation, ...]
    attributes: Tuple[Attribute, ...]

    @property
    def start(self) -> int:
        return self.span[0][0]

    @property
    def end(self) -> int:
        return self.span[-1][-1]


@dataclass
class Document(object):
    entities: List[Entity]
    relations: List[Relation]
    attributes: List[Attribute]


def parse(ann_path: str) -> Document:
    entities, relations, attributes = read_file_annotations(ann_path)
    return Document(list(entities), list(relations), list(attributes))


def parse_string(annotation_string: str) -> Document:
    annotations_s = "\n" + annotation_string
    annotations_s = re.sub(r"^#.+", "", annotations_s, flags=re.MULTILINE)
    annotations = remove_empty(re.split(r"\n([TRAE]\d+\t)", annotations_s))
    entities = list()
    relations = list()
    attributes = list()

    for i in range(0, len(annotations), 2):
        if annotations[i].startswith("T"):
            entity = parse_entity(annotations[i], annotations[i + 1])
            entities.append(entity)
        elif annotations[i].startswith("R"):
            relation = parse_relation(annotations[i], annotations[i + 1])
            relations.append(relation)
        elif annotations[i].startswith("A"):
            attribute = parse_attribute(annotations[i], annotations[i + 1])
            attributes.append(attribute)
    return Document(entities, relations, attributes)


def parse_string_to_augmented_entities(
    annotation_string: str,
) -> Dict[str, AugmentedEntity]:
    document = parse_string(annotation_string)
    augmented_entities: Dict[str, AugmentedEntity] = {}
    for entity in document.entities:
        entity_id = entity.id
        entity_relations_from_me = []
        entity_relations_to_me = []
        entity_attributes = []
        for relation in document.relations:
            if relation.subj == entity_id:
                entity_relations_from_me.append(relation)
            if relation.obj == entity_id:
                entity_relations_to_me.append(relation)
        for attribute in document.attributes:
            if attribute.target == entity_id:
                entity_attributes.append(attribute)
        augmented_entities[entity.id] = AugmentedEntity(
            id=entity.id,
            type=entity.type,
            span=entity.span,
            text=entity.text,
            relations_from_me=tuple(entity_relations_from_me),
            relations_to_me=tuple(entity_relations_to_me),
            attributes=tuple(entity_attributes),
        )
    return augmented_entities


def get_augmented_entities(ann_path: str) -> Dict[str, AugmentedEntity]:
    entities, relations, attributes, _ = get_entities_relations_attributes_groups(
        ann_path
    )
    augmented_entities = {}
    for entity_id, entity in entities.items():
        entity_relations_from_me = []
        entity_relations_to_me = []
        entity_attributes = []
        for _, relation in relations.items():
            if relation.subj == entity_id:
                entity_relations_from_me.append(relation)
            if relation.obj == entity_id:
                entity_relations_to_me.append(relation)
        for _, attribute in attributes.items():
            if attribute.target == entity_id:
                entity_attributes.append(attribute)
        augmented_entities[entity.id] = AugmentedEntity(
            id=entity.id,
            type=entity.type,
            span=entity.span,
            text=entity.text,
            relations_from_me=tuple(entity_relations_from_me),
            relations_to_me=tuple(entity_relations_to_me),
            attributes=tuple(entity_attributes),
        )
    return augmented_entities


def list_to_dict(s: List) -> Dict:
    return {i.id: i for i in s}


def get_entities_relations_attributes_groups(
    ann_path: str,
) -> Tuple[
    Dict[str, Entity], Dict[str, Relation], Dict[str, Attribute], Dict[str, Grouping],
]:
    entities_s, relations_s, attributes_s = read_file_annotations(ann_path)
    entities: Dict[str, Entity] = list_to_dict(entities_s)
    relations: Dict[str, Relation] = list_to_dict(relations_s)
    attributes: Dict[str, Attribute] = list_to_dict(attributes_s)

    # Process Groups

    grouping_relations = {
        r.id: r for r in relations.values() if r.type in GROUPING_RELATIONS
    }

    groups: Dict[str, Grouping] = {}

    for entity_id, entity in entities.items():
        if entity.type in GROUPING_ENTITIES:
            items: List[Entity] = list()
            for relation in grouping_relations.values():
                if relation.subj == entity_id:
                    items.append(entities[relation.obj])
            groups[entity_id] = Grouping(entity_id, entity.type, items)

    return entities, relations, attributes, groups


def parse_entity(tag_id: str, tag_content: str) -> Entity:
    """
    Parse the entity string into an Entity structure.

    Parameters
    ==========
    - tag_id : str
      The Tag ID in the annotation. (`T12\t` for example)
    - tag_content : str
      The tag text content. (`Temporal-Modifier 116 126\thistory of` for example)

    Returns
    =======
    - Entity
      An Entity object
    """
    tag_content = sanitize_tabs(tag_content, max_tabs=1)
    try:
        tag_spans, text = tag_content.strip().split("\t")
    except Exception as e:  # pragma: no cover
        print(tag_id)
        raise e
    tag = tag_spans.split(" ")[0].strip()
    spans_ = tag_spans[len(tag) :].split(";")
    spans: List[Tuple[int, int]] = []
    for span in spans_:
        start_s, end_s = span.split()
        start, end = int(start_s), int(end_s)
        spans.append((start, end))
    return Entity(tag_id.strip(), tag, tuple(spans), text)


def parse_relation(relation_id: str, relation_content: str) -> Relation:
    """
    Parse the annotation string into a Relation structure.

    Parameters
    ==========
    - relation_id : str
      The Relation ID in the annotation. (`R12\t` for example)
    - relation_content : str
      The relation text content. (`Modified-By Arg1:T8 Arg2:T6\t` for example)

    Returns
    =======
    - Relation
      A Relation object
    """
    try:
        relation, subj, obj = relation_content.strip().split()
    except Exception as e:
        print(relation_id)
        raise e
    subj = subj.replace("Arg1:", "")
    obj = obj.replace("Arg2:", "")
    return Relation(relation_id.strip(), relation, subj, obj)


def parse_attribute(attribute_id: str, attribute_content: str) -> Attribute:
    """
    Parse the annotation string into an Attribute structure.

    Parameters
    ==========
    - Attribute_id : str
      The attribute ID in the annotation. (`A1\t` for example)
    - Attribute_content : str
      The attribute text content. (`Tense T19 Past-Ended` for example)

    Returns
    =======
    - Attribute
      An Attribute object
    """
    attribute_arguments = attribute_content.strip().split(" ")
    if len(attribute_arguments) < 2:
        raise ValueError("The input attribute couldn't be parsed.")
    attribute_name = attribute_arguments[0]
    attribute_target = attribute_arguments[1]
    if len(attribute_arguments) == 2:
        return Attribute(attribute_id.strip(), attribute_name, attribute_target)
    # elif len(attribute_arguments) > 2:
    return Attribute(
        attribute_id.strip(),
        attribute_name,
        attribute_target,
        tuple(attribute_arguments[2:]),
    )


def read_file_annotations(
    ann: str,
) -> Tuple[List[Entity], List[Relation], List[Attribute]]:
    """
    Read an annotation file and get the Entities and Relations in it.

    Parameters
    ==========
    - ann : str
      The path to the annotation file to be processed.

    Returns
    =======
    - Tuple[Set[Entity], Set[Relation], Set[Attribute]]
      A tuple of sets of Entities, Relations, and Attributes.
    """
    ann_content = ""
    with open(ann, encoding="utf-8") as f:
        ann_content += f.read()
    document = parse_string(ann_content)
    return document.entities, document.relations, document.attributes
