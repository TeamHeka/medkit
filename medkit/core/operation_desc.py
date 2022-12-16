__all__ = ["OperationDescription"]

import dataclasses
from typing import Any, Dict


@dataclasses.dataclass
class OperationDescription:
    """Description of a specific instance of an operation

    Parameters
    ----------
    name:
        The name of the operation (typically the class name)
    uid:
        A unique identifier for the instance
    config:
        The specific configuration of the instance. Ideally, it
        should be possible to use that dict to reinstantiate the same
        operation
    """

    name: str
    uid: str
    config: Dict[str, Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(name=self.name, uid=self.uid, config=self.config)
