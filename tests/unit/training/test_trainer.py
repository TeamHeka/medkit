from medkit.core.trainable_operation import TrainableOperation
from medkit.training.trainer import TrainConfig, Trainer

from .dummy_context_operation.dummy_corpus import DUMMY_DATASETS
from .dummy_context_operation.dummy_operation import MockTrainableOperation


def test_trainable_op_runtime():
    mockTO = MockTrainableOperation()
    assert isinstance(mockTO, TrainableOperation)


def test_train(tmp_path):
    mockTO = MockTrainableOperation()
    output_dir = tmp_path / "dummy-operation"
    config = TrainConfig(output_dir=output_dir, batch_size=1)
    trainer = Trainer(
        mockTO,
        config=config,
        train_data=DUMMY_DATASETS["train"],
        eval_data=DUMMY_DATASETS["eval"],
    )
    trainer.train()
