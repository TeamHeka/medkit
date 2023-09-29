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


@pytest.mark.parametrize(
    "lr_scheduler_builder",
    [
        None,
        lambda optimizer: torch.optim.lr_scheduler.StepLR(
            optimizer, step_size=1, gamma=0.1
        ),
    ],
    ids=["default_no_lr_scheduler", "with_lr_scheduler"],
)
def test_trainer_checkpoint(tmp_path, lr_scheduler_builder):
    mock_component = MockTrainableComponent()
    output_dir = tmp_path / "full_model"
    config = TrainerConfig(
        output_dir=output_dir,
        batch_size=1,
        seed=0,
    )
    trainer = Trainer(
        mock_component,
        config=config,
        train_data=DUMMY_DATASETS["train"],
        eval_data=DUMMY_DATASETS["eval"],
        lr_scheduler_builder=lr_scheduler_builder,
    )
    trainer.train()

    path_checkpoint = list(output_dir.iterdir())[0]
    expected_optimizer_file = path_checkpoint / OPTIMIZER_NAME
    expected_config_file = path_checkpoint / CONFIG_NAME
    expected_scheduler_file = path_checkpoint / SCHEDULER_NAME
    assert expected_optimizer_file.exists()
    assert expected_config_file.exists()

    if lr_scheduler_builder is not None:
        assert expected_scheduler_file.exists()
    else:
        assert not expected_scheduler_file.exists()

    # testing model checkpoint
    # this is related to trainable component
    MockTrainableComponent(model_path=path_checkpoint)
