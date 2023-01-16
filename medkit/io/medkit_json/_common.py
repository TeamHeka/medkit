__all__ = [
    "MEDKIT_JSON_VERSION",
    "ContentType",
    "Modality",
    "build_header",
    "check_header",
]

import enum
from typing import Any, Dict


MEDKIT_JSON_VERSION = "0.1"


class Modality(enum.Enum):
    TEXT = "text"
    AUDIO = "audio"


class ContentType(enum.Enum):
    DOCUMENT = "document"
    DOCUMENT_LIST = "document_list"
    ANNOTATION_LIST = "annotation_list"


def build_header(content_type: ContentType, modality: Modality) -> Dict[str, Any]:
    return {
        "version": MEDKIT_JSON_VERSION,
        "content_type": content_type.value,
        "modality": modality.value,
    }


def check_header(data, expected_content_type: ContentType, expected_modality: Modality):
    # NB: when newer versions of the medkit json format are introduced,
    # migration functions will have to be implemented
    if data["version"] != MEDKIT_JSON_VERSION:
        raise RuntimeError("Input file has incompatible medkit version")

    content_type = ContentType(data["content_type"])
    if content_type is not expected_content_type:
        raise RuntimeError(
            f"Input file does not have expected {expected_content_type.value} content"
            f" type (has {content_type.value} instead)"
        )

    modality = Modality(data["modality"])
    if modality is not expected_modality:
        raise RuntimeError(
            f"Input file does not have expected {expected_modality.value} modality (has"
            f" {modality.value} instead)"
        )
