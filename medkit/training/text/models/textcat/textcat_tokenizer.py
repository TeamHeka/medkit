import dataclasses
from pathlib import Path

from tokenizers.implementations import ByteLevelBPETokenizer

DATA_PATH = Path(__file__).parent / ".tokenizer_pretrained"


@dataclasses.dataclass(frozen=True)
class DefaultConfig:
    vocab = "agnews-vocab.json"
    merges = "agnews-merges.txt"


class TextCatTokenizer:
    """Tokenizer for the TextCat model, it is based on ByteLevelBPETokenizer.
    It was trained with the agnews-dataset"""

    def __init__(self, config=DefaultConfig):
        vocab_filepath = str(DATA_PATH / config.vocab)
        merges_filepath = str(DATA_PATH / config.merges)
        self.tokenizer = ByteLevelBPETokenizer.from_file(
            vocab_filepath, merges_filepath
        )

    def get_input_ids(self, text):
        return self.tokenizer.encode(text).ids

    @property
    def vocab_size(self):
        return self.tokenizer.get_vocab_size()
