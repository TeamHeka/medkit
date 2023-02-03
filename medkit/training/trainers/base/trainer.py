import datetime
import logging
import os
import random
import time

from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np
import torch
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, Dataset

from medkit.core.trainable_operation import TrainableOperation
from medkit.training.trainers.base.train_config import TrainConfig
from medkit.training.utils import BatchData, MetricsCalculator
from medkit.training.callbacks import TrainerCallback, DefaultPrinterCallback

# checkpoint constants
OPTIMIZER_NAME = "optimizer.pt"
SCHEDULER_NAME = "scheduler.pt"


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def set_seed(seed: int = 0):
    """Set seed to keep deterministic operations"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class _TrainerDataset(Dataset):
    """Dataset to use in a TrainableOperation. This class is inspired from
    the ``PipelineDataset`` class from hugginface transformers library
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
    def __init__(
        self,
        operation: TrainableOperation,
        config: TrainConfig,
        train_data: Any,
        eval_data: Any,
        metrics_calculator: Optional[MetricsCalculator] = None,
        lr_scheduler_builder: Optional[Callable[[torch.optim.Optimizer], Any]] = None,
        callback: Optional[TrainerCallback] = None,
    ):
        # enable deterministic operation
        set_seed(0)

        self.output_dir = (
            Path(config.output_dir)
            if config.output_dir
            else operation.__class__.__name__
        )
        os.makedirs(self.output_dir, exist_ok=True)

        self.operation = operation
        self.batch_size = config.batch_size
        self.dataloader_drop_last = False
        self.dataloader_num_workers = config.dataloader_num_workers
        self.dataloader_pin_memory = False

        self.device = self.operation.device

        self.train_dataloader = self.get_dataloader(train_data, shuffle=True)
        self.eval_dataloader = self.get_dataloader(eval_data, shuffle=False)
        self.num_train_epochs = config.num_training_epochs

        # config with some optional params
        self.config = config

        self.optimizer, self.lr_scheduler = self.create_optimizer_and_scheduler(
            self.operation, config.learning_rate, lr_scheduler_builder
        )
        self.metrics_calculator = metrics_calculator

        if callback is None:
            self.callback = DefaultPrinterCallback()

    def get_dataloader(self, data: any, shuffle: bool) -> DataLoader:
        # prepare data: we could add a data processor here
        dataset = _TrainerDataset(data, self.operation)
        collate_fn = self.operation.collate
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle,
            collate_fn=collate_fn,
            drop_last=self.dataloader_drop_last,
            num_workers=self.dataloader_num_workers,
            pin_memory=self.dataloader_pin_memory,
        )

    @staticmethod
    def create_optimizer_and_scheduler(
        operation: TrainableOperation,
        lr: float,
        lr_scheduler_builder: Optional[Callable[[torch.optim.Optimizer], Any]],
    ) -> Tuple[torch.optim.Optimizer, Optional[Any]]:
        optimizer = operation.configure_optimizer(lr=lr)

        if lr_scheduler_builder is not None:
            lr_scheduler = lr_scheduler_builder(optimizer)
        else:
            lr_scheduler = None

        return optimizer, lr_scheduler

    def training_epoch(self) -> Dict[str, Dict[str, float]]:
        config = self.config
        total_loss_epoch = 0.0
        data_for_metrics = defaultdict(list)

        self.callback.on_epoch_begin()

        for step, samples in enumerate(self.train_dataloader):
            # train step begin
            model_output, loss = self.make_forward_pass(
                samples, return_loss=True, eval_mode=False
            )

            if config.gradient_accumulation_steps > 1:
                loss = loss / config.gradient_accumulation_steps

            loss.backward()

            if ((step + 1) % config.gradient_accumulation_steps == 0) or (
                step + 1 == len(self.train_dataloader)
            ):
                self.optimizer.step()
                self.optimizer.zero_grad()

            total_loss_epoch += loss.item()

            if config.do_metrics_in_training and self.metrics_calculator is not None:
                prepared_batch = self.metrics_calculator.prepare_batch(
                    model_output, samples
                )
                for key, values in prepared_batch.items():
                    data_for_metrics[key].append(values)
            # train step end

        total_loss_epoch /= len(self.train_dataloader)
        metrics = {"train": {}}
        metrics["train"]["loss"] = total_loss_epoch

        if config.do_metrics_in_training and self.metrics_calculator is not None:
            metrics["train"].update(
                self.metrics_calculator.compute(dict(data_for_metrics))
            )
        return metrics

    def evaluation_epoch(self, eval_dataloader) -> Dict[str, Dict[str, float]]:
        total_loss_epoch = 0.0
        data_for_metrics = defaultdict(list)

        self.callback.on_epoch_begin()

        with torch.no_grad():
            for _, samples in enumerate(eval_dataloader):
                # eval step begin
                model_output, loss = self.make_forward_pass(
                    samples, return_loss=True, eval_mode=True
                )
                total_loss_epoch += loss.item()

                if self.metrics_calculator is not None:
                    prepared_batch = self.metrics_calculator.prepare_batch(
                        model_output, samples
                    )
                    for key, values in prepared_batch.items():
                        data_for_metrics[key].append(values)
                # eval step end

        total_loss_epoch /= len(self.train_dataloader)
        metrics = {"eval": {}}
        metrics["eval"]["loss"] = total_loss_epoch

        if self.metrics_calculator is not None:
            metrics["eval"].update(
                self.metrics_calculator.compute(dict(data_for_metrics))
            )
        return metrics

    def make_forward_pass(
        self, inputs: BatchData, return_loss: bool, eval_mode=bool
    ) -> Tuple[BatchData, Optional[torch.Tensor]]:
        inputs = inputs.to_device(self.device)
        model_output, loss = self.operation.forward(
            inputs, return_loss=return_loss, eval_mode=eval_mode
        )

        if return_loss and loss is None:
            raise ValueError("The operation did not return a 'loss' from the input.")

        return model_output, loss

    def update_learning_rate(self, eval_metrics: Dict[str, float]):
        if self.lr_scheduler is None:
            return

        if isinstance(self.lr_scheduler, ReduceLROnPlateau):
            metric_to_track_lr = eval_metrics["eval"].get(
                self.config.metric_to_track_lr
            )
            if metric_to_track_lr is None:
                raise RuntimeError(
                    "Learning schedule needs a eval metric to update the learning rate,"
                    " `None` was found"
                )
            self.lr_scheduler.step(metric_to_track_lr)
        else:
            self.lr_scheduler.step()

    def train(self):
        logger.info("---Running training---")
        logger.info(f" Num epochs = {self.config.num_training_epochs}")
        logger.info(f" Train batch size = {self.batch_size}")
        logger.info(
            f" Gradient Accum steps = {self.config.gradient_accumulation_steps}"
        )

        self.callback.on_train_begin()

        for epoch in range(1, self.num_train_epochs + 1):
            epoch_start_time = time.time()
            train_metrics = self.training_epoch()

            self.callback.on_epoch_end()
            self.callback.on_log(
                logger=logger,
                metrics=train_metrics,
                epoch_state=dict(
                    epoch=epoch, time_epoch=time.time() - epoch_start_time
                ),
            )

            epoch_start_time = time.time()
            eval_metrics = self.evaluation_epoch(self.eval_dataloader)

            self.callback.on_epoch_end()
            self.callback.on_log(
                logger=logger,
                metrics=eval_metrics,
                epoch_state=dict(
                    epoch=epoch, time_epoch=time.time() - epoch_start_time
                ),
            )

            self.update_learning_rate(eval_metrics)

        current_date = datetime.datetime.now().strftime("%d-%m-%Y_%H:%M")
        self.save_checkpoint(f"checkpoint_{current_date}")
        logger.info("Training is completed")
        self.callback.on_train_end()

    def save_checkpoint(self, name):
        """Save a trainer state. It saves the optimizer, scheduler and model state"""

        checkpoint_dir = os.path.join(self.output_dir, name)
        logger.info(f"Saving checkpoint in {checkpoint_dir}")

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
