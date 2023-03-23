# Core components

This page contains all core concepts of medkit.

:::{note}
For more details about public APIs, refer to {mod}`medkit.core`.
:::

## Documents, Annotations & Attributes

Medkit documents classes are used to:
* access to raw data,
* store relevant annotations extracted from the raw data.

The {class}`~.core.Document` and {class}`~.core.annotation.Annotation` protocols
are defined inside {mod}`medkit.core`. They define common properties and
methods across all modalities. These protocols are then implemented for each
modality (text, audio, image, etc), with additional logic specific to the
modality.

To facilitate the implementation of the {class}`~.core.Document` protocol,
an {class}`~.core.AnnotationContainer` class is provided. It behaves like a list of
annotations, with additional filtering methods and support for non-memory
storage.

{mod}`medkit.core` also defines the {class}`~.core.Attribute` class, that
can directly be used to attach attributes to annotations of any modality.
Similarly to {class}`~.core.AnnotationContainer`, the role of this container is to
provide additional methods for facilitating access to the list of attributes
belonging to an annotation.

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

Currently, {mod}`medkit.core.text` implements a
{class}`~.text.TextDocument` class and a corresponding set of
{class}`~.text.TextAnnotation` subclasses, and similarly
{mod}`medkit.core.audio` provides an {class}`~.audio.AudioDocument` class
and a corresponding {class}`~medkit.core.audio.annotation.Segment`.
Both modality also subclass {class}`~.core.AnnotationContainer` to add some
modality-specific logic or filtering.

To get more details about each modality, you can refer to their documentation:
* [core text](core_text.md)
* [core audio](core_audio.md)

(api:core:document)=
### Document

{class}`~.core.Document` protocol class provides the minimal data structure
for a medkit document.
For example, each document (whatever the modality) is linked to an annotation
container for the same modality.

{class}`~.core.AnnotationContainer` class provides a set of methods (e.g., add/get)
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

:::{note}
For more details about their implementation, refer to
{class}`medkit.core.document.Document` and
{class}`medkit.core.annotation_container.AnnotationContainer`.
:::

(api:core:annotation)=
### Annotation & Attribute

{class}`~medkit.core.annotation.Annotation` protocol class provides the minimal
data structure for a medkit annotation.

For example, each annotation is linked to an attribute container.

{class}`~.core.AttributeContainer` class provides a set of common interfaces for
accessing to the annotation {class}`~.core.Attribute` whatever the modality.

Given an annotation `ann` from any modality:

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

### Collection

{class}`~.core.Collection` class allows to manipulate a set of {class}`~.core.Document`.

:::{warning}
This work is still under development. It may be changed in the future.
:::

(api:core:operations)=
## Operations

The {class}`~.core.Operation` abstract class groups all necessary methods for
being compatible with medkit processing pipeline and provenance.

We have defined different subclasses depending on the nature of the operation,
including text-specific and audio-specific operations in {mod}`medkit.core.text`
and {mod}`medkit.core.audio`.

To get more details about each modality, you can refer to their documentation:
* [core text](core_text.md)
* [core audio](core_audio.md)


For all operations inheriting from {class}`~.core.Operation` abstract class,
these 4 lines shall be added in `__init__` method:
```
def __init__(self, ..., uid=None):
    ...
    # Pass all arguments to super (remove self)
    init_args = locals()
    init_args.pop("self")
    super().__init__(**init_args)
```

Each operation is described with {class}`~.core.OperationDescription`.




## Converters

Two abstract classes have been defined for managing document conversion
between medkit format and another one.

:::{note}
For more details about the public APIs, refer to {mod}`medkit.core.conversion`.
:::


(api:core:pipeline)=
## Pipeline

{class}`~.core.Pipeline` allows to chain several operations.

To better understand how to declare and use medkit pipelines, you may refer
to the [pipeline tutorial](../user_guide/pipeline).

:::{note}
For more details about the public APIs, refer to {mod}`medkit.core.pipeline`.
:::

The {class}`~medkit.core.doc_pipeline.DocPipeline` class is a wrapper allowing
to run an annotation pipeline on a list of documents by automatically attach
output annotations to these documents.

## Store

A store is an object responsible for keeping the annotations of a document
(through an {class}`~.core.AnnotationContainer`) or the attributes of an
annotation (through an {class}`~.core.AttributeContainer`).

The {class}`~medkit.core.store.Store` protocol defines the method that a store
must implement. For now, we only provide a single implement of this protocol
based on a dictionary, but in the future we will probably provide other
implementations relying on databases.

Users can also implement their own store based on their needs.

:::{warning}
This work is still under development. It may be changed in the future.
:::

:::{note}
For more details about the public APIs, refer to {mod}`medkit.core.store`.
:::

### Global store

To store all data items in the same location, a global store is used for your
application.
If you have not set your own store, the global store will automatically use the
simple internal dict store.

If you implement your own store, we suggest to call
{meth}`medkit.core.store.GlobalStore.init_store` before initializing any other
medkit  component.

{class}`~.core.GlobalStore` provides initialization, access and removal methods
for the global store.

(api:core:provenance)=
## Provenance

:::{warning}
This work is still under development. It may be changed in the future.
:::

Provenance is a medkit concept allowing to track all operations and
their role in new knowledge extraction.

With this mechanism, we will be able to provide the provenance information
about a generated data. To log this information, a separate provenance
store is used.

For better understanding this concept, you may follow the
[provenance tutorial](../user_guide/provenance) and/or refer to
["how to make your own module"](../user_guide/module) to know what you have to
do to enable provenance.

:::{note}
For more details about the public APIs, refer to {mod}`medkit.core.prov_tracer`.
:::
