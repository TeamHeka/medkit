# Core text components

This page contains all core text concepts of medkit.

## Document, Annotations & Attributes

The {class}`~medkit.core.text.document.TextDocument` class implements the
{class}`~medkit.core.Document` protocol. It allows to store subclasses of
{class}`~medkit.core.text.annotation.TextAnnotation`, which implements the
{class}`~medkit.core.Annotation` protocol. Three subclasses are defined:
{class}`~medkit.core.text.annotation.Segment`,
{class}`~medkit.core.text.annotation.Entity` and
{class}`~medkit.core.text.annotation.Relation`

`TextDocument` relies on {class}`~medkit.core.text.document.TextAnnotationContainer`, a
subclass of {class}`~medkit.core.AnnotationContainer`, to store the annotations,

```{mermaid}
:align: center
:caption: Text document and annotation hierarchy

classDiagram
    direction TD
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
    TextAnnotation <|-- Segment 
    TextAnnotation <|-- Relation
    Segment <|-- Entity
```

### Document

```{eval-rst}
.. automodule:: medkit.core.text.document
    :members:
    :inherited-members:
```

### Annotations

```{eval-rst}
.. automodule:: medkit.core.text.annotation
    :members:
    :inherited-members:
```

### Attributes

Text annotations can receive attributes, which will be instances of the core
{class}`~medkit.core.Attribute` class.

`medkit.core.text` defines
{class}`~medkit.core.text.normalization.EntityNormalization`, to be used for
values of normalization attributes, in order to have a common structure for
normalization information, independently of the operation used to create it.

```{eval-rst}
.. automodule:: medkit.core.text.normalization
    :members:
    :inherited-members:
```

(api:core-text:span)=
## Spans

```{eval-rst}
.. automodule:: medkit.core.text.span
    :members:
```

## Span utilities

:::{seealso}
cf. [spans notebook example](../examples/spans).
:::

```{eval-rst}
.. automodule:: medkit.core.text.span_utils
    :members:
```

## Text utilities

These utilities have some preconfigured patterns for preprocessing text documents without destruction. They are not really supposed to be used directly, but rather inside a cleaning operation.

:::{seealso}
 Medkit provides the {class}`~medkit.text.preprocessing.eds_cleaner.EDSCleaner` class that combines all these utilities to clean french documents (related to EDS documents coming from PDF).
:::

```{eval-rst}
.. automodule:: medkit.core.text.utils
    :members:
```

## Operations

Abstract sub-classes of `Operation` have been defined for text to ease the
development of text operations according to `run` operations.

```{eval-rst}
.. automodule:: medkit.core.text.operation
    :members: ContextOperation, NEROperation, SegmentationOperation
```

### Custom operations

You can also use the following function for instantiating a custom text operation.

```{eval-rst}
.. autofunction:: medkit.core.text.operation.create_text_operation
.. autoclass:: medkit.core.text.operation.CustomTextOpType
```
