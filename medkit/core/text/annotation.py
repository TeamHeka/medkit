__all__ = ["Entity", "Attribute", "Relation"]

from medkit.core.annotation import Annotation


class Entity(Annotation):
    def __init__(self, origin_id, label, spans, text, entity_id=None, metadata=None):
        """
        Initialize a medkit text entity

        Parameters
        ----------
        origin_id: str
            The id of the operation which creates this entity
            (i.e., ProcessingDescription.id)
        label: str
            The entity label
        spans: List[Span]
            The entity span
        text: str
            The entity text
        entity_id: str, Optional
            The id of the entity (if existing)
        metadata: dict[str, Any], Optional
            The metadata of the entity
        """
        super().__init__(
            ann_id=entity_id, origin_id=origin_id, label=label, metadata=metadata
        )
        self.spans = spans
        self.text = text

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, spans={self.spans!r}, text={self.text!r}"


class Attribute(Annotation):
    def __init__(
        self, origin_id, label, target_id, value=None, attr_id=None, metadata=None
    ):
        """
        Initialize a medkit attribute

        Parameters
        ----------
        origin_id: str
            The id of the operation which creates this attribute
            (i.e., ProcessingDescription.id)
        label: str
            The attribute label
        target_id: str
            The id of the entity on which the attribute is applied
        value: str, Optional
            The value of the attribute
        attr_id: str, Optional
            The id of the attribute (if existing)
        metadata: Dict[str, Any], Optional
            The metadata of the attribute
        """
        super().__init__(
            ann_id=attr_id, origin_id=origin_id, label=label, metadata=metadata
        )
        self.target_id = target_id
        self.value = value

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, target_id={self.target_id!r}, value={self.value}"


class Relation(Annotation):
    def __init__(
        self, origin_id, label, source_id, target_id, rel_id=None, metadata=None
    ):
        """
        Initialize the medkit relation

        Parameters
        ----------
         origin_id: str
            The id of the operation which creates this relation
            (i.e., ProcessingDescription.id)
        label: str
            The relation label
        source_id: str
            The id of the entity from which the relation is defined
        target_id: str
            The id of the entity to which the relation is defined
        rel_id: str, Optional
            The id of the relation (if existing)
        metadata: Dict[str, Any], Optional
            The metadata of the relation
        """
        super().__init__(
            ann_id=rel_id, origin_id=origin_id, label=label, metadata=metadata
        )
        self.source_id = source_id
        self.target_id = target_id

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, source={self.source_id}, target_id={self.target_id}"
