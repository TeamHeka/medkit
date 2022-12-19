__all__ = ["OperationDescription"]

import dataclasses
from typing import Any, Dict, Optional


@dataclasses.dataclass
class OperationDescription:
    """Description of a specific instance of an operation

    Parameters
    ----------
    uid:
        The unique identifier of the instance described
    class_name:
        The name of the class of the operation
    name:
        The name of the operation. If `None`, class name will be used. This is
        useful for operations with a behavior that can be customized (for
        instance a rule-based entity matcher with user-provided rules, or a
        model-based entity matcher with a user-provided model). In that case it
        is possible to describe the operation with a name more specific than the
        class name.
    config:
        The specific configuration of the instance
    """

    uid: str
    class_name: str
    name: Optional[str] = None
    config: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if self.name is None:
            self.name = self.class_name

    def to_dict(self) -> Dict[str, Any]:
        return dict(
            uid=self.uid, class_name=self.class_name, name=self.name, config=self.config
        )
