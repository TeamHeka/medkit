# Training module

This page describes all components related to the medkit training.

:::{important}
For using this module, you need to install [PyTorch](https://pytorch.org/).
You may install additional dependencies using
`pip install medkit[training]`.
:::

:::{note}
For more details about all sub-packages, refer to {mod}`medkit.training`.
:::

## Trainable Operations

The medkit {class}`~.training.TrainableOperation` protocol describes all the
necessary methods to make an operation trainable in medkit.

:::{important}
Currently, medkit only supports the training of operations using **PyTorch**
models.
:::

:::{note}
For more details, refer to {mod}`medkit.training.trainable_operation` module.
:::

## Trainer

The {class}`~.training.Trainer` aims to train any {class}`~.training.TrainableOperation`.
Therefore, it is possible to customise it using the {class}`~.training.TrainerConfig`.

The {class}`~.training.Trainer` contains two optional parameters `metrics_computer`
and `lr_scheduler_builder` to define the way metrics are calculated and how the
learning rate is updated.


:::{note}
For more details, refer to {mod}`medkit.training.trainer` module.
:::

## Utils

medkit provides utils for managing batch data and metrics computing for training.

:::{note}
For more details, refer to {mod}`medkit.training.utils` module.
:::

## Callbacks

medkit provides a set of callbacks that can be used if you want to do some
stuff like logging information.

For using these callbacks, you need to implement a class derived from
{class}`~.training.TrainerCallback`.

If you do not provide your own one to the {class}`~.training.Trainer`, it will
use the {class}`~.training.DefaultPrinterCallback`.

:::{note}
For more details, refer to {mod}`medkit.training.callbacks` module.
:::
