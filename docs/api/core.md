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
to `AnnotationContainer`, the role of this container is to provide additional
methods for facilitating access to the list of attributes belonging to an
annotation.

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
    Document *-- Annotation : contains\n(AnnotationContainer)
    Annotation *-- Attribute : contains\n(AttributeContainer)
```

Currently, `medkit.core.text` implements a
{class}`~medkit.core.text.TextDocument` class and a corresponding set of
{class}`~medkit.core.text.TextAnnotation` subclasses, and similarly
`medkit.core.audio` provides an {class}`~medkit.core.audio.AudioDocument` class
and a corresponding {class}`~medkit.core.audio.Segment`. Both modality also
subclass `AnnotationContainer` to add some modality-specific logic or filtering.

To get more details about each modality, you can refer to their documentation:
* [core text](core_text.md)
* [core audio](core_audio.md)


(api:core:document)=
### Document

`Document` protocol class provides the minimal data structure for a medkit
document.
For example, each document (whatever the modality) is linked to an annotation
container for the same modality.

`AnnotationContainer` class provides a set of methods (e.g., add/get)
to be implemented for each modality.

The goal is to provide user with a minimum set of common interfaces for
accessing to the document annotations whatever the modality.

Given a document named `doc` from any modality

* User can browse the document annotations
  ```
  for ann in doc.anns:
    ...
  ```
* User can add a new annotation to the document
  ```
  ann = <my annotation>
  doc.anns.add(ann)
  ```
* User can get the document annotations filtered by label
  ```
  anns = doc.anns.get(label="disorder")
  ```

---

```{eval-rst}
.. autoclass:: medkit.core::Document
    :members:
```

---

```{eval-rst}
.. autoclass:: medkit.core::AnnotationContainer
    :members:
```

(api:core:annotation)=
### Annotation

`Annotation` protocol class provides the minimal data structure for a medkit
annotation.

For example, each annotation is linked to an attribute container.

`AttributeContainer` class provides a set of common interfaces for accessing to
the annotation attributes whatever the modality.

Given an annotation `ann` from any modality

* User may browse the annotation attributes
  ```
  for attr in ann.attrs:
    ...
  ```
* User may add a new attribute to an annotation
  ```
  attr = <my attribute>
  ann.attrs.add(attr)
  ```
* User may get the annotation attributes filtered by label
  ```
  attrs = ann.attrs.get(label="NORMALIZATION")
  ```

---

```{eval-rst}
.. autotypevar:: medkit.core::AnnotationType
    :no-type:
 ```

---

```{eval-rst}
.. autoclass:: medkit.core.annotation::Annotation
    :members:
```

---

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

We have defined different subclasses depending on the nature of the operation,
including text-specific and audio-specific operations in `medkit.core.text` and
`medkit.core.audio`.

To get more details about each modality, you can refer to their documentation:
* [core text](core_text.md)
* [core audio](core_audio.md)


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

---

```{eval-rst}
.. autoclass:: medkit.core::Operation
    :members:
```

---
Each operation is described as follows:

```{eval-rst}
.. autoclass:: medkit.core::OperationDescription
    :members:
```

## Converters

Two abstract classes have been defined for managing document conversion
between medkit format and another one.

---

```{eval-rst}
.. autoclass:: medkit.core::InputConverter
    :members:
```

---

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

---

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

A store is an object responsible for keeping the annotations of a document
(through an {class}`~medkit.core.AnnotationContainer`) or the attributes of an
annotation (through an {class}`~medkit.core.AttributeContainer`).

The {class}`~medkit.core.Store` protocol defines the method that a store must
implement. For now we only provide a single implement of this protocol based on
a dictionary, but in the future we will probably provide other implementations
relying on databases.

Users can also implement their own store based on their needs.

:::{warning}
This work is still under development. It may be changed in the future.
:::

```{eval-rst}
.. autoclass:: medkit.core::Store
    :members:
```
### Global store

To store all data items in the same location, a global store is used for your application.
If you have not set your own store, the global store will automatically use the simple internal dict store.

If you implement your own store, we suggest to call `Global.initstore` before initializing any medkit other component.
The following class provides initialization, access and removal methods for the global store:

````{eval-rst}
.. autoclass:: medkit.core::GlobalStore
    :members:
````

(api:core:provenance)=
## Provenance

Provenance is a medkit concept allowing to track all operations and
their role in new knowledge extraction.
With this mechanism, we will be able to provide the provenance information
about a generated data. To log this information, a separate provenance
store is used.

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

---

```{eval-rst}
.. autoclass:: medkit.core::Prov
    :members:
```
