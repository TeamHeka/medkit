# dataset POC for training
__all__ = ["AG_NEWS"]
from typing import Literal

import numpy as np
import pandas as pd
from torch.utils.data import Dataset

from medkit.core.annotation import Attribute
from medkit.core.text import Segment, Span

# Pytorch could present memory problems if the dtypes are not defined or
# the main file on the dataset use a list to keep the samples

# some tools for this module


def _to_numpy(series, type_):
    return np.asarray(series).astype(type_)


def _process_chunk(df_chunk):
    # join columns (pandas returns 2 columns because they are separated using ',')
    df_chunk["text"] = df_chunk.iloc[:, 1] + df_chunk.iloc[:, 2]
    label_id = _to_numpy(df_chunk.iloc[:, 0], int)
    text = _to_numpy(df_chunk["text"], np.str_)
    del df_chunk
    return label_id, text


def _numpy_from_csv(url):
    dtype_corpus = {0: int, 1: "string", 2: "string"}
    labels = []
    texts = []
    for chunk in pd.read_csv(url, header=None, dtype=dtype_corpus, chunksize=10000):
        label_id, text = _process_chunk(chunk)
        labels.append(label_id)
        texts.append(text)
    return np.hstack(labels), np.hstack(texts)


_URL = {
    "train": "https://raw.githubusercontent.com/mhjabreel/CharCnn_Keras/master/data/ag_news_csv/train.csv",
    "test": "https://raw.githubusercontent.com/mhjabreel/CharCnn_Keras/master/data/ag_news_csv/test.csv",
}

_DESCRIPTION: str = (
    "AG News (AG's News Corpus) is a subdataset of AG's corpus of news articles"
    " constructed by assembling titles and description fields of articles from the 4"
    " largest classes (“World”, “Sports”, “Business”, “Sci/Tech”) of AG's Corpus. The"
    " AG News contains 30,000 training and 1,900 test samples per class."
    " More info: https://paperswithcode.com/dataset/ag-news"
)


class AG_NEWS(Dataset):
    # simulate an annotated corpus
    def __init__(self, split: Literal["train", "test"]):
        print(f"Creating AG_NEWS corpus {split}")
        self.description = _DESCRIPTION
        self.labels_id, self.text = _numpy_from_csv(_URL[split])

        self.attr_label = "category"
        self.id2label = {1: "World", 2: "Sports", 3: "Business", 4: "Sci/Tec"}

        print(
            f"Size corpus in Mem: {self.text.nbytes/1024**2} ,"
            f" {self.labels_id.nbytes/1024**2}"
        )
        print(f"Datatype of nparray: {self.text.dtype} , {self.labels_id.dtype}")

    def __len__(self):
        return len(self.labels_id)

    def __getitem__(self, idx):
        label_id = self.labels_id[idx]
        text = self.text[idx]
        medkit_object = self._format_to_medkit(label_id, text)
        return medkit_object

    def _format_to_medkit(self, label_id, text):
        # simulate a segment
        segment = Segment(text=text, label="raw_segment", spans=[Span(0, len(text))])
        segment.add_attr(
            Attribute(label=self.attr_label, value=self.id2label[label_id])
        )
        return segment
