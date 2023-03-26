from __future__ import annotations

__all__ = ["Trainer"]

import datetime
import os
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import torch
import yaml
from medkit.training.trainer_config import TrainerConfig
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, Dataset

from medkit.training.trainable_operation import TrainableOperation
from medkit.training.callbacks import DefaultPrinterCallback, TrainerCallback
from medkit.training.utils import BatchData, MetricsComputer

# checkpoint constants
OPTIMIZER_NAME = "optimizer.pt"
SCHEDULER_NAME = "scheduler.pt"
CONFIG_NAME = "config.yml"


def set_seed(seed: int = 0):
    """Set seed to keep deterministic operations"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class _TrainerDataset(Dataset):
    """A Dataset that preprocesses data using the 'preprocess' defined in a trainable operation.
    This class is inspired from the ``PipelineDataset`` class from hugginface transformers library.
    """

    def __init__(self, dataset, operation: TrainableOperation):
        self.dataset = dataset
        self.operation = operation

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, i):
        item = self.dataset[i]
        processed = self.operation.preprocess(item, inference_mode=False)
        return processed


class Trainer:
    """A trainer is a base training/eval loop for a TrainableOperation that uses PyTorch models
    to create medkit annotations
    """

    def __init__(
        self,
        operation: TrainableOperation,
        config: TrainerConfig,
        train_data: Any,
        eval_data: Any,
        metrics_computer: Optional[MetricsComputer] = None,
        lr_scheduler_builder: Optional[Callable[[torch.optim.Optimizer], Any]] = None,
        callback: Optional[TrainerCallback] = None,
    ):
        """
        Parameters
        ----------
        operation:
            The operation to train, the operation must implement the `TrainableOperation` protocol.
        config:
            A `TrainerConfig` with the parameters for training, the parameter `output_dir` define the
            path of the checkpoints
        train_data:
            The data to use for training. This should be a corpus of medkit objects. The data could be,
            for instance, a `torch.utils.data.Dataset` that returns medkit objects for training.
        eval_data:
            The data to use for evaluation, this is not for testing. This should be a corpus of medkit objects.
            The data can be a `torch.utils.data.Dataset` that returns medkit objects for evaluation.
        metrics_computer:
            Optional `MetricsComputer` object that will be used to compute custom metrics during eval.
            By default, only evaluation metrics will be computed, `do_metrics_in_training` in `config` allows
            metrics in training.
        lr_scheduler_builder:
            Optional function that build a `lr_scheduler` to adjust the learning rate after an epoch. Must take
            an Optimizer and return a `lr_scheduler`. If not provided, the learning rate does not change during training.
        callback:
            Optional callback to customize training.
        """
        # enable deterministic operation
        if config.seed is not None:
            set_seed(config.seed)

        self.output_dir = Path(config.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        self.operation = operation
        self.batch_size = config.batch_size
        self.dataloader_drop_last = False
        self.dataloader_nb_workers = config.dataloader_nb_workers
        self.dataloader_pin_memory = False

        self.device = self.operation.device

        self.train_dataloader = self.get_dataloader(train_data, shuffle=True)
        self.eval_dataloader = self.get_dataloader(eval_data, shuffle=False)
        self.nb_training_epochs = config.nb_training_epochs

        self.config = config

        self.optimizer = operation.configure_optimizer(self.config.learning_rate)
        self.lr_scheduler = (
            None
            if lr_scheduler_builder is None
            else lr_scheduler_builder(self.optimizer)
        )

        self.metrics_computer = metrics_computer

        if callback is None:
            self.callback = DefaultPrinterCallback()

    def get_dataloader(self, data: any, shuffle: bool) -> DataLoader:
        """Return a DataLoader with transformations defined
        in the operation to train"""
        dataset = _TrainerDataset(data, self.operation)
        collate_fn = self.operation.collate
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle,
            collate_fn=collate_fn,
            drop_last=self.dataloader_drop_last,
            num_workers=self.dataloader_nb_workers,
            pin_memory=self.dataloader_pin_memory,
        )

    def training_epoch(self) -> Dict[str, float]:
        """
        Perform an epoch using the training data.

        When the config enabled metrics in training ('do_metrics_in_training' is True),
        the additional metrics are prepared per batch.

        Return a dictionary with metrics.
        """
        config = self.config
        total_loss_epoch = 0.0
        metrics = {}
        data_for_metrics = defaultdict(list)

        for step, input_batch in enumerate(self.train_dataloader):
            self.callback.on_step_begin(step)

            model_output, loss = self.make_forward_pass(input_batch, eval_mode=False)

            if config.gradient_accumulation_steps > 1:
                loss = loss / config.gradient_accumulation_steps

            loss.backward()

            if ((step + 1) % config.gradient_accumulation_steps == 0) or (
                step + 1 == len(self.train_dataloader)
            ):
                self.optimizer.step()
                self.optimizer.zero_grad()

            total_loss_epoch += loss.item()

            if config.do_metrics_in_training and self.metrics_computer is not None:
                prepared_batch = self.metrics_computer.prepare_batch(
                    model_output, input_batch
                )
                for key, values in prepared_batch.items():
                    data_for_metrics[key].append(values)

            self.callback.on_step_end(
                step, nb_batches=len(self.train_dataloader), phase="train"
            )

        total_loss_epoch /= len(self.train_dataloader)
        metrics["loss"] = total_loss_epoch

        if config.do_metrics_in_training and self.metrics_computer is not None:
            metrics.update(self.metrics_computer.compute(dict(data_for_metrics)))
        return metrics

    def evaluation_epoch(self, eval_dataloader) -> Dict[str, float]:
        """
        Perform an epoch using the evaluation data.

        The additional metrics are prepared per batch.
        Return a dictionary with metrics.
        """
        total_loss_epoch = 0.0
        metrics = {}
        data_for_metrics = defaultdict(list)

        with torch.no_grad():
            for step, input_batch in enumerate(eval_dataloader):
                self.callback.on_step_begin(step)

                model_output, loss = self.make_forward_pass(input_batch, eval_mode=True)
                total_loss_epoch += loss.item()

                if self.metrics_computer is not None:
                    prepared_batch = self.metrics_computer.prepare_batch(
                        model_output, input_batch
                    )
                    for key, values in prepared_batch.items():
                        data_for_metrics[key].append(values)

                self.callback.on_step_end(
                    step, nb_batches=len(eval_dataloader), phase="eval"
                )

        total_loss_epoch /= len(self.eval_dataloader)
        metrics["loss"] = total_loss_epoch

        if self.metrics_computer is not None:
            metrics.update(self.metrics_computer.compute(dict(data_for_metrics)))
        return metrics

    def make_forward_pass(
        self, inputs: BatchData, eval_mode: bool
    ) -> Tuple[BatchData, torch.Tensor]:
        """Run forward safely, same device as the operation"""
        inputs = inputs.to_device(self.device)
        model_output, loss = self.operation.forward(
            inputs, return_loss=True, eval_mode=eval_mode
        )

        if loss is None:
            raise ValueError("The operation did not return a 'loss' from the input.")

        return model_output, loss

    def update_learning_rate(self, eval_metrics: Dict[str, float]):
        """Call the learning rate scheduler if defined"""
        if self.lr_scheduler is None:
            return

        if isinstance(self.lr_scheduler, ReduceLROnPlateau):
            name_metric_to_track_lr = self.config.metric_to_track_lr
            eval_metric = eval_metrics.get(name_metric_to_track_lr)
            if eval_metric is None:
                raise ValueError(
                    "Learning scheduler needs an eval metric to update the learning"
                    f" rate, '{name_metric_to_track_lr}' was not found"
                )
            self.lr_scheduler.step(eval_metric)
        else:
            self.lr_scheduler.step()

    def train(self) -> List[Dict]:
        """
        Main training method. Call the training / eval loop.

        Return a list with the metrics per epoch.
        """
        self.callback.on_train_begin(config=self.config)
        log_history = []

        for epoch in range(1, self.nb_training_epochs + 1):
            epoch_start_time = time.time()
            self.callback.on_epoch_begin()

            train_metrics = self.training_epoch()

            eval_metrics = self.evaluation_epoch(self.eval_dataloader)
            self.update_learning_rate(eval_metrics)

            metrics = {"train": train_metrics, "eval": eval_metrics}
            log_history.append(metrics)

            self.callback.on_epoch_end(
                metrics=metrics,
                epoch=epoch,
                epoch_duration=time.time() - epoch_start_time,
            )
        self.save()
        self.callback.on_train_end()
        return log_history

    def save(self):
        """Save a final checkpoint and the trainer configuration"""
        current_date = datetime.datetime.now().strftime("%d-%m-%Y_%H:%M")
        name = f"checkpoint_{current_date}"

        self.save_checkpoint(name)

        # save config
        config_path = os.path.join(self.output_dir, name, CONFIG_NAME)
        with open(str(config_path), mode="w") as fp:
            yaml.safe_dump(
                self.config.to_dict(),
                fp,
                encoding="utf-8",
                allow_unicode=True,
                sort_keys=False,
            )

    def save_checkpoint(self, name):
        """Save a trainer state. It saves the optimizer, scheduler"""

        checkpoint_dir = os.path.join(self.output_dir, name)
        self.callback.on_save(checkpoint_dir=checkpoint_dir)

        os.makedirs(checkpoint_dir, exist_ok=True)
        torch.save(
            self.optimizer.state_dict(), os.path.join(checkpoint_dir, OPTIMIZER_NAME)
        )

        if self.lr_scheduler is not None:
            torch.save(
                self.lr_scheduler.state_dict(),
                os.path.join(checkpoint_dir, SCHEDULER_NAME),
            )

        self.operation.save(checkpoint_dir)