from dataclasses import dataclass, field


@dataclass
class TextCatConfig:
    vocab_size: int
    embed_dim: int = field(default=128)
    num_class: int = field(default=4)
