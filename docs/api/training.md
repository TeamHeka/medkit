# Training module

This page describes all components related to medkit training.

:::{important}
For using this module, you need to install [PyTorch](https://pytorch.org/).
You may install additional dependencies using
`pip install medkit-lib[training]`.
:::

:::{note}
For more details about all sub-packages, refer to {mod}`medkit.training`.
:::

## Be `trainable` in medkit

A component can implement the {class}`~.training.TrainableComponent` protocol to be trainable in medkit. With this protocol, you can define how to preprocess data, call the model and define the optimizer. Then, the {class}`~.training.Trainer` will use these methods inside the training / evaluation loop. 

A trainable component could define how to train a model from scratch or fine-tune a pretrained model. As a first implementation, medkit includes {class}`~.text.ner.hf_entity_matcher_trainable.HFEntityMatcherTrainable`, a trainable version of {class}`~.text.ner.hf_entity_matcher.HFEntityMatcher`. As you can see, an operation can contains a trainable component and expose it using the `make_trainable()` method. 


:::{important}
Currently, medkit only supports the training of components using **PyTorch**
components.
:::

:::{note}
For more details, refer to {mod}`medkit.training.trainable_component` module.
:::

## Trainer

The {class}`~.training.Trainer` aims to train any component implementing the {class}`~.training.TrainableComponent` protocol.

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
