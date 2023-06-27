__all__ = ["generate_id", "generate_deterministic_id"]

import uuid
import random


def generate_id() -> str:
    return str(uuid.uuid1())


def generate_deterministic_id(reference_id: str):
    # generate deterministic uuid based on reference_id
    # so the generated uid is the same if the reference_id is the same
    rng = random.Random(reference_id)
    uid = uuid.UUID(int=rng.getrandbits(128))
    return uid
