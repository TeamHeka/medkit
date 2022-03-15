__all__ = ["generate_id"]

import uuid


def generate_id() -> str:
    return str(uuid.uuid1())
