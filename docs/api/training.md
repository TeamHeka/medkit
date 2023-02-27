# Training module

For using this module, you need to install [PyTorch](https://pytorch.org/).

This page describes all components related to the training of `TrainableOperation` in medkit.

## Trainer

The `Trainer` aims to train any `TrainableOperation`. Therefore, it is possible to customise it using the `TrainerConfig`. 

The `Trainer` contains two optional parameters `metrics_computer` and `lr_scheduler_builder` to define the way metrics are calculated and how the learning rate is updated.

```{eval-rst}
.. automodule:: medkit.training.trainer
    :members:
```

## Utils
```{eval-rst}
.. automodule:: medkit.training.utils
    :members:
```

## Callbacks
The `Trainer` uses a `DefaultPrinterCallback` if none is provided.

```{eval-rst}
.. automodule:: medkit.training.callbacks
    :members:
```

