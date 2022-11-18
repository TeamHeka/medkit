import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader
from transformers.optimization import SchedulerType, get_scheduler

from medkit.core.trainable_operation import TrainableOperation
from medkit.training.metrics import Metric
from medkit.training.utils import BatchData, MedkitDataset

from .train_config import TrainConfig

logger = logging.getLogger(__name__)


def set_seed(seed: int = 0):
    """Set seed to keep deterministic operations"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# checkpoint constants
OPTIMIZER_NAME = "optimizer.pt"
SCHEDULER_NAME = "scheduler.pt"


class Trainer:
    def __init__(
        self,
        operation: TrainableOperation,
        config: TrainConfig,
        train_data: Any,
        eval_data: Any,
        metric: Optional[Metric] = None,
    ):
        # enable deterministic operation
        set_seed()

        self.output_dir = Path(config.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        self.operation = operation
        self.batch_size = config.batch_size
        self.dataloader_drop_last = False
        self.dataloader_num_workers = config.dataloader_num_workers
        self.dataloader_pin_memory = False

        self.device = torch.device(config.device)

        self.train_dataloader = self.get_dataloader(train_data)
        self.eval_dataloader = self.get_dataloader(eval_data)
        self.logging_interval = config.logging_interval
        self.num_train_epochs = config.num_training_epochs

        # config with some optional params
        self.config = config

        # model to device
        self.operation.to(self.device)
        self.optimizer, self.lr_scheduler = self.create_optimizer_and_scheduler(
            self.operation, config
        )
        self.metric = metric

    def get_dataloader(self, train_data: any):
        # prepare data: we could add a data processor here
        medkit_dataset = MedkitDataset(
            train_data, self.operation.preprocess, {"inference_mode": False}
        )
        collate_fn = self.operation.collate_fn
        return DataLoader(
            medkit_dataset,
            batch_size=self.batch_size,
            shuffle=True,
            collate_fn=collate_fn,
            drop_last=self.dataloader_drop_last,
            num_workers=self.dataloader_num_workers,
            pin_memory=self.dataloader_pin_memory,
        )

    @staticmethod
    def create_optimizer_and_scheduler(
        operation: TrainableOperation, train_cfg: TrainConfig
    ):
        optimizer = operation.configure_optimizer(lr=train_cfg.learning_rate)
        lr_scheduler_type = train_cfg.lr_scheduler_type

        if lr_scheduler_type in list(SchedulerType):
            lr_scheduler = get_scheduler(
                name=lr_scheduler_type,
                optimizer=optimizer,
                num_warmup_steps=train_cfg.num_warmup_steps,
                num_training_steps=train_cfg.num_training_steps,
            )
        elif lr_scheduler_type == "reduce_lr_with_metric":
            lr_scheduler = ReduceLROnPlateau(optimizer)
        else:
            raise ValueError(f"{lr_scheduler_type} is not a valid scheduler type")
        return optimizer, lr_scheduler

    def data_to_device(self, data: BatchData) -> Dict[str, torch.Tensor]:
        return {k: item.to(self.device) for k, item in data.items()}

    def training_epoch(self, epoch_idx: int):
        config = self.config
        total_loss_epoch = 0.0
        # steps_in_training = 0
        # len_dataloader = len(self.train_dataloader)
        # on train epoch begin
        for step, samples in enumerate(self.train_dataloader):
            # on train step begin

            _samples = self.data_to_device(samples)
            model_output = self.ensure_model_output(_samples, eval_mode=False)
            loss = model_output.loss

            if config.gradient_accumulation_steps > 1:
                loss = loss / config.gradient_accumulation_steps

            loss.backward()

            if ((step + 1) % config.gradient_accumulation_steps == 0) or (
                step + 1 == len(self.train_dataloader)
            ):
                self.optimizer.step()
                self.optimizer.zero_grad()

            total_loss_epoch += loss.item()

            # do metrics
            self.metric.add_batch(model_output, _samples)

            # on train step end
            if (step + 1) % self.logging_interval == 0:
                metrics_msg = f"{self.metric.name}: {self.metric.compute():8.3f}"
                print(
                    "| epoch {} | steps {} | {}".format(
                        epoch_idx,
                        step + 1,
                        metrics_msg,
                    )
                )
        total_loss_epoch /= len(self.train_dataloader)
        return total_loss_epoch

    def evaluation_epoch(self, eval_dataloader):
        total_epoch_loss = 0.0
        self.metric.reset()
        with torch.no_grad():
            for _, samples in enumerate(eval_dataloader):
                _samples = self.data_to_device(samples)
                model_output = self.ensure_model_output(_samples, eval_mode=True)
                total_epoch_loss += model_output.loss.item()
                self.metric.add_batch(model_output, _samples)

        total_metrics = {self.metric.name: self.metric.compute()}

        total_epoch_loss /= len(eval_dataloader)
        total_metrics["total_eval_loss"] = total_epoch_loss
        return total_metrics

    def update_learning_rate(self, metric_to_track: Optional[float] = None):
        if isinstance(self.lr_scheduler, ReduceLROnPlateau):
            if metric_to_track is None:
                raise RuntimeError(
                    "Learning schedule needs a metric to update the learning rate,"
                    " `None` was provided"
                )
            self.lr_scheduler.step(metric_to_track)
        else:
            self.lr_scheduler.step()

    def train(self):
        for epoch in range(1, self.num_train_epochs + 1):
            epoch_start_time = time.time()
            total_train_loss = self.training_epoch(epoch)

            metrics = self.evaluation_epoch(self.eval_dataloader)
            metric_to_track = metrics.get(self.metric.name)
            self.update_learning_rate(metric_to_track)

            # on
            print("-" * 59)
            print(
                "| end of epoch {:3d} | time: {:5.2f}s | valid accuracy {:8.3f} "
                .format(epoch, time.time() - epoch_start_time, metric_to_track)
            )
            print(
                "train loss: {:8.3f}, eval loss: {:8.3f}".format(
                    total_train_loss, metrics.get("total_eval_loss")
                )
            )
            print("-" * 59)

        self.save_checkpoint(epoch)

    def ensure_model_output(self, samples: Dict[str, torch.tensor], eval_mode: bool):
        model_output = self.operation.forward(samples, eval_mode=eval_mode)

        if "loss" not in model_output:
            raise ValueError(
                "The operation did not return a 'loss' from the input. Please see"
                " 'operation.forward' method."
            )

        return model_output

    def save_checkpoint(self, epoch_idx: int):
        """Save a trainer state. It saves the optimizer, scheduler and model state"""

        checkpoint_dir = os.path.join(self.output_dir, f"checkpoint_epoch_{epoch_idx}")
        logger.info(f"Saving checkpoint in {checkpoint_dir}")

        os.makedirs(checkpoint_dir, exist_ok=True)
        torch.save(
            self.optimizer.state_dict(), os.path.join(checkpoint_dir, OPTIMIZER_NAME)
        )

        torch.save(
            self.lr_scheduler.state_dict(), os.path.join(checkpoint_dir, SCHEDULER_NAME)
        )

        self.operation.save(checkpoint_dir)
