import logging


class TrainerCallback:
    """A TrainerCallback is the base class for trainer callbacks"""

    def on_init_end(self):
        """Event called at the end of the initialization of a Trainer"""
        pass

    def on_train_begin(self):
        """Event called at the beginning of training"""
        pass

    def on_train_end(self):
        """Event called at the end of training"""
        pass

    def on_epoch_begin(self):
        """Event called at the beginning of an epoch"""
        pass

    def on_epoch_end(self):
        """Event called at the end of an epoch"""
        pass

    def on_step_begin(self):
        """Event called at the beginning of a step in training"""
        pass

    def on_step_end(self):
        """Event called at the end of a step in training"""
        pass

    def on_save(self):
        """Event called on saving a checkpoint"""
        pass


class DefaultPrinterCallback(TrainerCallback):
    def __init__(self):
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # define handler and formatter
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def on_init_end(self):
        self.logger.info("Trainer has been configured correctly")

    def on_train_begin(self, config):
        self.logger.info("---Running training---")
        self.logger.info(f" Num epochs = {config.nb_training_epochs}")
        self.logger.info(f" Train batch size = {config.batch_size}")
        self.logger.info(
            f" Gradient Accum steps = {config.gradient_accumulation_steps}"
        )

    def on_epoch_end(self, metrics, epoch, epoch_time):
        logger = self.logger

        train_metrics = metrics.get("train", None)
        if train_metrics is not None:
            logger.info("-" * 59)
            msg = "|".join(
                f"{metric_key}:{value:8.3f}"
                for metric_key, value in train_metrics.items()
            )
            logger.info(f"Training metrics : {msg}")

        eval_metrics = metrics.get("eval", None)
        if eval_metrics is not None:
            msg = "|".join(
                f"{metric_key}:{value:8.3f}"
                for metric_key, value in eval_metrics.items()
            )
            logger.info(f"Evaluation metrics : {msg}")
            logger.info("-" * 59)

        logger.info(
            "Epoch state: |epoch_id: {:3d} | time: {:5.2f}s".format(epoch, epoch_time)
        )

    def on_train_end(self):
        self.logger.info("Training is completed")

    def on_save(self, checkpoint_dir):
        self.logger.info(f"Saving checkpoint in {checkpoint_dir}")
