import torch

from medkit.core import Attribute
from medkit.core.text import Segment, Span

texts_training = [
    "La prise en charge thérapeutique ne sera pas modifiée par l'étude",
    "La prise en charge thérapeutique sera modifiée par l'étude",
    "La patient est malade",
    "La patient n'est pas malade",
    "L'objectif est de comparer l'efficacité et la tolérance de la gemcitabine",
    "Compte de rendu medical",
]
labels_training = ["neg", "pos", "pos", "neg", "pos", "pos"]

texts_eval = ["Elle ne prend pas de médicament", "Elle a une prescription"]
labels_eval = ["neg", "pos"]


class DummyCorpus(torch.utils.data.Dataset):
    def __init__(self, texts, labels):
        self.texts = texts
        self.labels = labels
        self.attr_label = "category"

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        segment = Segment(text=text, label="raw_segment", spans=[Span(0, len(text))])
        segment.add_attr(Attribute(label=self.attr_label, value=label))
        return segment

    def __len__(self):
        return len(self.labels)


DUMMY_DATASETS = {
    "train": DummyCorpus(texts_training, labels_training),
    "eval": DummyCorpus(texts_eval, labels_eval),
}
