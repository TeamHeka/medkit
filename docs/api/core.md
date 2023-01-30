# Core components

This page contains all core concepts of medkit.

## Documents, Annotations & Attributes

Medkit documents classes are used to:
* access to raw data,
* store relevant annotations extracted from the raw data.

The {class}`~medkit.core.Document` and {class}`~medkit.core.Annotation`
protocols are defined inside `medkit.core`. They define common properties and
methods across all modalities. These protocols are then implemented for each
modality (text, audio, image, etc), with additional logic specific to the
modality.

To facilitate the implementation of the `Document` protocol, an
{class}`~medkit.core.AnnotationContainer` class is provided. It behaves like a
list of annotations, with additional filtering methods and support for
non-memory storage.

`medkit.core` also defines the {class}`~medkit.core.Attribute` class, that can
directly be used to attach attributes to annotations of any modality. Similarly
to `AnnotationContainer`, an {class}`~medkit.core.AttributeContainer` class is
provided to be reused when implementing `Annotation` for a specific modality.

```{mermaid}
:align: center
:caption: Core protocols and classes

classDiagram
    direction LR
    class Document~Annotation~{
        <<protocol>>
        uid: str
        anns: AnnotationContainer~Annotation~
    }
    class AnnotationContainer~Annotation~{
    }
    class Annotation{
        <<protocol>>
        uid: str
        label: str
        attrs: AttributeContainer
    }
    class Attribute{
        uid: str
        label: str
        value: Optional[Any]
    }
    class AttributeContainer{
    }
    Document .. AnnotationContainer
    AnnotationContainer o-- Annotation
    AttributeContainer o-- Attribute
    Annotation .. AttributeContainer
```

Currently, `medkit.core.text` implements a
{class}`~medkit.core.text.TextDocument` class and a corresponding set of
{class}`~medkit.core.text.TextAnnotation` subclasses, and similarly
`medkit.core.text` provides an {class}`~medkit.core.text.AudioDocument` class
and a corresponding {class}`~medkit.core.text.AudioSegment`. Both modality also
subclass `AnnotationContainer` to add some modality-specific logic or filtering.

```{mermaid}
:align: center
:caption: Modality-specific classes

classDiagram
    direction LR
    class TextDocument{
        uid: str
        anns: TextAnnotationContainer
    }
    class TextAnnotationContainer{
    }
    class TextAnnotation{
        <<abstract>>
        uid: str
        label: str
        attrs: AttributeContainer
    }
    TextDocument *-- TextAnnotationContainer
    TextAnnotationContainer o-- TextAnnotation
    TextAnnotation <|-- TextSegment 
    TextAnnotation <|-- Relation
    TextSegment <|-- Entity

    class AudioDocument{
        uid: str
        anns: AudioAnnotationContainer
    }
    class AudioAnnotationContainer{
    }
    class AudioSegment {
        uid: str
        label: str
        attrs: AttributeContainer
    }
    AudioDocument *-- AudioAnnotationContainer
    AudioAnnotationContainer o-- AudioSegment
    AudioSegment
```

### Document


```{eval-rst}
.. autoclass:: medkit.core::Document
    :members:
```

```{eval-rst}
.. autotypevar:: medkit.core.document::AnnotationType
    :no-type:
 ```

```{eval-rst}
.. autoclass:: medkit.core::AnnotationContainer
    :members:
```

```{eval-rst}
.. autotypevar:: medkit.core.annotation_container::AnnotationType
    :no-type:
 ```

### Annotation

```{eval-rst}
.. autoclass:: medkit.core::Annotation
    :members:
```

```{eval-rst}
.. autoclass:: medkit.core::AttributeContainer
    :members:
```

### Attribute

(api:core:attribute)=
```{eval-rst}
.. autoclass:: medkit.core::Attribute
    :members:
```

### Collection

:::{warning}
This work is still under development. It may be changed in the future.
:::

```{eval-rst}
.. autoclass:: medkit.core::Collection
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
def __init__(self, ..., uid=None):
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
To see an example of pipeline usage, you may refer to the [pipeline tutorial](../user_guide/pipeline).
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

## Store

A store is an object responsible of keeping the annotations of a document
(through an {class}`~medkit.core.AnnotationContainer`) or the attributes of an
annotation (through an {class}`~medkit.core.AttributeContainer`).

The {class}`~medkit.core.Store` protocol defines the method that a store must
implement. For now we only provide a single implement of this protocol based on
a dictionnary, {class}`~medkit.core.DictStore` but in the future we will
probably provide other implementations relying on databases.

Users can also implement their own store based on their needs.

:::{warning}
This work is still under development. It may be changed in the future.
:::

```{eval-rst}
.. autoclass:: medkit.core::Store
    :members:
```

```{eval-rst}
.. autoclass:: medkit.core::DictStore
    :members:
```

(api:core:provenance)=
## Provenance

Provenance is a medkit concept allowing to track all operations and
their role in new knowledge extraction.
With this mechanism, we will be able to provide the provenance information
about a generated data.

:::{important}
Please refer to the [provenance tutorial](../user_guide/provenance) and ["how to make your own
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
