import pytest

torch = pytest.importorskip(modname="torch", reason="torch is not installed")

from medkit.training import TrainerConfig, Trainer  # noqa: E402
from medkit.training.trainer import (
    OPTIMIZER_NAME,
    CONFIG_NAME,
    SCHEDULER_NAME,
)  # noqa: E402

from .dummy_context_component.dummy_corpus import DUMMY_DATASETS  # noqa: E402
from .dummy_context_component.dummy_component import (
    MockTrainableComponent,
)  # noqa: E402


class DummyMetricsComputer:
    """Mock accuracy metrics Computer with pre-determined values"""

    def __init__(self, minimize):
        self._epoch = 0
        # decrease during 3 epochs then overfit
        if minimize:
            self._scores = [1.0, 0.9, 0.8, 0.85]
        else:
            self._scores = [0.1, 0.2, 0.3, 0.25]

    def prepare_batch(self, model_output, input_batch):
        return {}

    def compute(self, all_data):
        score = self._scores[self._epoch]
        self._epoch += 1
        return {"accuracy": score}


def _check_checkpoint(path, use_lr_scheduler):
    expected_optimizer_file = path / OPTIMIZER_NAME
    expected_config_file = path / CONFIG_NAME
    expected_scheduler_file = path / SCHEDULER_NAME
    assert expected_optimizer_file.exists()
    assert expected_config_file.exists()
    if use_lr_scheduler:
        assert expected_scheduler_file.exists()
    else:
        assert not expected_scheduler_file.exists()

    # testing model checkpoint
    # this is related to trainable component
    MockTrainableComponent(model_path=path)


@pytest.mark.parametrize(
    "use_lr_scheduler,minimize_metric,overfit",
    [
        # no scheduler, minimize metric, overfit
        (False, True, True),
        # scheduler, minimize metric, overfit
        (True, True, True),
        # no scheduler, maximize metric, overfit
        (False, False, True),
        # only 3 epochs, no overfit (best model is also last model)
        (False, True, False),
    ],
    ids=["default", "with_lr_scheduler", "maximize_metric", "overfit"],
)
def test_trainer_checkpoint(tmp_path, use_lr_scheduler, minimize_metric, overfit):
    def lr_scheduler_builder(optimizer):
        return torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.1)

    mock_component = MockTrainableComponent()
    output_dir = tmp_path / "full_model"
    config = TrainerConfig(
        output_dir=output_dir,
        nb_training_epochs=4 if overfit else 3,
        batch_size=1,
        checkpoint_metric="accuracy",
        minimize_checkpoint_metric=minimize_metric,
    )
    trainer = Trainer(
        mock_component,
        config=config,
        train_data=DUMMY_DATASETS["train"],
        eval_data=DUMMY_DATASETS["eval"],
        lr_scheduler_builder=lr_scheduler_builder if use_lr_scheduler else None,
        metrics_computer=DummyMetricsComputer(minimize=minimize_metric),
    )
    trainer.train()

    checkpoints_paths = sorted(output_dir.iterdir())
    for path in checkpoints_paths:
        _check_checkpoint(path, use_lr_scheduler)

    # 2 checkpoints must be saved: the best and the last
    # unless they are the same
    if overfit:
        assert len(checkpoints_paths) == 2
        best_checkpoint, last_checkpoint = checkpoints_paths
        assert best_checkpoint.name.startswith("checkpoint_003")
        assert last_checkpoint.name.startswith("checkpoint_004")
    else:
        # when we don't overfit, the last is also the best
        assert len(checkpoints_paths) == 1
        assert checkpoints_paths[0].name.startswith("checkpoint_003")
