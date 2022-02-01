__all__ = ["Entity", "Attribute", "Relation"]

from medkit.core.annotation import Annotation


class Entity(Annotation):
    def __init__(self, origin, label, spans, text):
        super().__init__(origin=origin, label=label)
        self.spans = spans
        self.text = text

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, spans={self.spans!r}, text={self.text!r}"


class Attribute(Annotation):
    def __init__(self, origin, label, target_id, value=None):
        super().__init__(origin=origin, label=label)
        self.target_id = target_id
        self.value = value

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, target_id={self.target_id!r}, value={self.value}"


class Relation(Annotation):
    def __init__(self, origin, label, source_id, target_id):
        super().__init__(origin=origin, label=label)
        self.source_id = source_id
        self.target_id = target_id

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, source={self.source_id}, target_id={self.target_id}"
