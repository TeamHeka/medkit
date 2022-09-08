# Core classes

This page contains all core concepts of medkit.

## Document & Annotations

The `Document` class allows medkit to:
* access to raw data,
* store relevant annotations extracted from the raw data.

The `Document` class is an abstract class which will be inherited by
different modalities (e.g., text, audio, images, ...).
`TextDocument` and `AudioDocument` derive `Document` for text and audio usecases.

```{eval-rst}
.. autoclasstree:: medkit.core.text.document medkit.core.document medkit.core.audio.document
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Document hierarchy
```

```{eval-rst}
.. autoclass:: medkit.core::Document
    :members:
```

```{eval-rst}
.. autotypevar:: medkit.core.document::AnnotationType
    :no-type:
 ```

The `Collection` class is under construction.

```{eval-rst}
.. autoclass:: medkit.core::Collection
    :members:
```


### Annotation

The `Annotation` abstract class provides common methods for every
annotation type.
An annotation may contain a list of [Attributes](api:core:attribute).

We have several text and audio annotation classes in respectively `medkit.core.text` and `medkit.core.audio`,
each one with its own data structure.

```{eval-rst}
.. autoclasstree:: medkit.core.annotation medkit.core.text.annotation medkit.core.audio.annotation
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Annotation hierarchy (TODO: fix this schema to remove the audio/text Segment confusion)
```

```{eval-rst}
.. autoclass:: medkit.core::Annotation
    :members:
```

(api:core:attribute)=
```{eval-rst}
.. autoclass:: medkit.core::Attribute
    :members:
```

(api:core:operations)=
## Operations

The medkit `Operation` abstract class groups all necessary methods for
being compatible with medkit processing pipeline and provenance.

We have defined different sub-classes depending on the nature of the operation,
including text-specific and audio-specific operations in `medkit.core.text` and `medkit.core.audio`.
Here is a graph representing this hierarchy:

```{eval-rst}
.. autoclasstree:: medkit.core.operation medkit.core.text.operation medkit.core.audio.operation
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Operation hierarchy (TODO: fix this schema to remove confusion between audio/text operations)
```

For all operations inheriting from `Operation` abstract class, these 4 lines
shall be added in `__init__` method:
```
def __init__(self, ..., op_id=None):
    ...
    # Pass all arguments to super (remove self)
    init_args = locals()
    init_args.pop("self")
    super().__init__(**init_args)
```

```{eval-rst}
.. autoclass:: medkit.core::Operation
    :members:
```

Each operation is described as follows:

```{eval-rst}
.. autoclass:: medkit.core::OperationDescription
    :members:
```

## Converters

Two abstract classes have been defined for managing document conversion
between medkit format and another one.

```{eval-rst}
.. autoclass:: medkit.core::InputConverter
    :members:
```

```{eval-rst}
.. autoclass:: medkit.core::OutputConverter
    :members:
```

(api:core:pipeline)=
## Pipeline

:::{seealso}
To see an example of pipeline usage, you may refer to [demo](../examples/demo).
:::

```{eval-rst}
.. autoclass:: medkit.core::Pipeline
    :members:
```

```{eval-rst}
.. autoclass:: medkit.core::PipelineStep
    :members:
```

### High-level: Doc pipeline

The `DocPipeline` class allows to run a pipeline on a list of documents.

```{eval-rst}
.. autoclass:: medkit.core::DocPipeline
    :members:
```

(api:core:provenance)=
## Provenance & Store

Provenance & store are medkit concepts allowing to track all operations and
their role in new knowledge extraction.
With this mechanism, we will be able to provide the provenance information
about a generated data.

:::{important}
Please refer to [demo example](../examples/demo) and ["how to make your own
module"](../user_guide/module) to know what you have to do to enable
provenance.
:::

:::{warning}
This work is still under development. It may be changed in the future.
:::

```{eval-rst}
.. autoclass:: medkit.core::ProvTracer
    :members:
```

```{eval-rst}
.. autoclass:: medkit.core::Prov
    :members:
```

```{eval-rst}
.. autoclass:: medkit.core::Store
    :members:
```

```{eval-rst}
.. autoclass:: medkit.core::DictStore
    :members:
```
