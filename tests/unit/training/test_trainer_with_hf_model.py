import shutil

import pytest
import transformers

from medkit.core.text.annotation import Entity, Segment
from medkit.core.text.span import Span
from medkit.text.ner.hf_entity_matcher_trainable import HFEntityMatcherTrainable
from medkit.training import Trainer, TrainerConfig

_TOKENIZER_MAX_LENGTH = 24
_MODEL_NER_CLINICAL = "samrawal/bert-base-uncased_clinical-ner"


# Creating a tiny model with the original vocabulary
@pytest.fixture(autouse=True)
def create_model_and_tokenizer(tmp_path):
    tokenizer = transformers.BertTokenizerFast.from_pretrained(
        _MODEL_NER_CLINICAL, model_max_length=32
    )  # modify the original config to make a tiny model with the original vocab
    config = transformers.BertConfig.from_pretrained(_MODEL_NER_CLINICAL)
    config.update(
        dict(
            vocab_size=tokenizer.vocab_size,
            hidden_size=20,
            num_hidden_layers=1,
            num_attention_heads=1,
            intermediate_size=10,
            max_position_embeddings=32,
        )
    )

    model = transformers.BertForTokenClassification(config=config)
    # save model and tokenizer
    model.save_pretrained(tmp_path / "tiny_bert")
    tokenizer.save_pretrained(tmp_path / "tiny_bert")


def _create_tiny_data(pairs_text_entities):
    data = []
    for text, ents in pairs_text_entities:
        segment = Segment(text=text, spans=[Span(0, len(text))], label="sentence")
        entities = [
            Entity(label=e[0], text=text[e[1] : e[2]], spans=[Span(e[1], e[2])])
            for e in ents
        ]
        data += [[segment, entities]]
    return data


@pytest.fixture()
def train_data():
    return _create_tiny_data(
        [
            ("Voici un examen", [("test", 9, 15)]),
            ("Le patient vomit ", [("problem", 11, 16)]),
            ("L'IRM a été effectuée", [("test", 2, 5)]),
            ["Sous anesthésie générale", [("treatment", 5, 24)]],
        ]
    )


@pytest.fixture()
def eval_data():
    return _create_tiny_data(
        [
            ("Le scanner a été trouvé", [("test", 9, 15)]),
            ("Douleur", [("problem", 0, 7)]),
        ]
    )


def test_trainer_default(train_data, eval_data, tmp_path):
    matcher = HFEntityMatcherTrainable(
        model_name_or_path=tmp_path / "tiny_bert",
        labels=["problem", "treatment", "test"],
        tagging_scheme="iob2",
        tokenizer_max_length=_TOKENIZER_MAX_LENGTH,
    )
    output_dir = tmp_path / "trained_model"
    config = TrainerConfig(
        output_dir=output_dir,
        batch_size=1,
        learning_rate=5e-6,
        nb_training_epochs=1,
    )

    trainer = Trainer(
        operation=matcher, config=config, train_data=train_data, eval_data=eval_data
    )

    log_history = trainer.train()
    assert len(log_history) == config.nb_training_epochs

    eval_item = next(iter(trainer.eval_dataloader))
    assert list(eval_item["input_ids"].size()) == [1, _TOKENIZER_MAX_LENGTH]

    # [FIX] remove model to prevent writing error (cache-pytest)
    shutil.rmtree(output_dir)
