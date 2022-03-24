__all__ = ["TextItem", "get_text_items", "Generator", "Prefixer", "Splitter", "Merger"]

from medkit.core import generate_id


class TextItem:
    def __init__(self, text):
        """Mock text item with id"""

        self.id = generate_id()
        self.text = text


def get_text_items(nb_items):
    return [TextItem(f"This is the text item number {i}.") for i in range(nb_items)]


class Generator:
    def __init__(self, prov_builder=None):
        """Mock operation generating text items"""

        self.id = generate_id()
        self.prov_builder = prov_builder

    def generate(self, nb_items):
        items = get_text_items(nb_items)
        if self.prov_builder is not None:
            for item in items:
                self.prov_builder.add_prov(item.id, self.id, source_ids=[])
        return items


class Prefixer:
    def __init__(self, prov_builder=None):
        """Mock operation prefixing items"""

        self.id = generate_id()
        self.prov_builder = prov_builder

    def prefix(self, items):
        prefixed_items = []
        for item in items:
            prefixed_item = TextItem("Hello! " + item.text)
            prefixed_items.append(prefixed_item)
            if self.prov_builder is not None:
                self.prov_builder.add_prov(
                    prefixed_item.id, self.id, source_ids=[item.id]
                )
        return prefixed_items


class Splitter:
    def __init__(self, prov_builder=None):
        """Mock operation splitting items"""

        self.id = generate_id()
        self.prov_builder = prov_builder

    def split(self, items):
        split_items = []
        for item in items:
            half = len(item.text) // 2
            left_item = TextItem(item.text[:half])
            split_items.append(left_item)
            right_item = TextItem(item.text[half:])
            split_items.append(right_item)

            if self.prov_builder is not None:
                self.prov_builder.add_prov(left_item.id, self.id, source_ids=[item.id])
                self.prov_builder.add_prov(right_item.id, self.id, source_ids=[item.id])
        return split_items


class Merger:
    """Mock operation merging items"""

    def __init__(self, prov_builder=None):
        self.id = generate_id()
        self.prov_builder = prov_builder

    def merge(self, items):
        text = "".join(s.text for s in items)
        merged_item = TextItem(text)
        if self.prov_builder is not None:
            self.prov_builder.add_prov(
                merged_item.id, self.id, source_ids=[s.id for s in items]
            )
        return merged_item
