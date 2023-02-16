# Core text components

This page contains all core text concepts of medkit.

## Document, Annotations & Attributes

The {class}`~medkit.core.text.document.TextDocument` class implements the
{class}`~medkit.core.Document` protocol. It allows to store subclasses of
{class}`~medkit.core.text.annotation.TextAnnotation`, which implements the
{class}`~medkit.core.Annotation` protocol. 


```{mermaid}
:align: center
:caption: Text document and text annotation

classDiagram
     direction TB
     class Document~Annotation~{
        <<protocol>>
    }
    class Annotation{
        <<protocol>>
    }
    class TextDocument{
        uid: str
        anns: TextAnnotationContainer
    }
    class TextAnnotation{
        <<abstract>>
        uid: str
        label: str
        attrs: AttributeContainer
    }
    Document <|.. TextDocument: implements
    Annotation <|.. TextAnnotation: implements
    TextDocument *-- TextAnnotation: contains \n(TextAnnotationContainer)
```

### Document

`TextDocument` relies on {class}`~medkit.core.text.TextAnnotationContainer`, a
subclass of {class}`~medkit.core.AnnotationContainer`, to manage the annotations,

Given a text document named `doc`

* User can browse segments, entities, and relations
  ```
  for entity in doc.anns.entities:
    ...
  
  for segment in doc.anns.segments:
    ...
  
  for relation in doc.anns.relations:
    ...
  ```
* User can filter segments, entities and relations
  ```
    sentences_segments = doc.get_segments(label="sentences")
    disorder_entities = doc.get_entities(label="disorder)
    
    entity = <my entity>
    relations = doc.get_relations(label="before", source_id=entity.uid)
  ```

```{note}
For common interfaces provided by core components, you can refer to
[Document](api:core:document).
```

```{eval-rst}
.. autoclass:: medkit.core.text::TextDocument
    :members:
```
---
```{eval-rst}
.. autoclass:: medkit.core.text::TextAnnotationContainer
    :members:
```
### Annotations

For text modality, `TextDocument` can only contain 
{class}`~medkit.core.text.TextAnnotation`.

Three subclasses are defined:
{class}`~medkit.core.text.annotation.Segment`,
{class}`~medkit.core.text.annotation.Entity` and
{class}`~medkit.core.text.annotation.Relation`

```{mermaid}
:align: center
:caption: Text annotation hierarchy

classDiagram
     direction TB
    class Annotation{
        <<protocol>>
    }
    class TextAnnotation{
        <<abstract>>
    }
    Annotation <|.. TextAnnotation: implements
    TextAnnotation <|-- Segment 
    TextAnnotation <|-- Relation
    Segment <|-- Entity
```

```{note}
Each text annotation class inherits from the common interfaces provided by the
core component (cf. [Annotation](api:core:annotation))
```

```{eval-rst}
.. autoclass:: medkit.core.text::TextAnnotation
    :members:
```
---
```{eval-rst}
.. autoclass:: medkit.core.text::Segment
    :members:
```
---
```{eval-rst}
.. autoclass:: medkit.core.text::Entity
    :members:
```
---
```{eval-rst}
.. autoclass:: medkit.core.text::Relation
    :members:
```


### Attributes

Text annotations can receive attributes, which will be instances of the core
{class}`~medkit.core.Attribute` class.

---
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

Abstract subclasses of `Operation` have been defined for text to ease the
development of text operations according to `run` operations.

```{note}
Refer to [custom operations](api:core:text:custom_op) for more details on how
to use internal class `_CustomTextOperation`.
```

```{eval-rst}
.. autoclasstree:: medkit.core.operation medkit.core.text.operation
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Operation hierarchy
```

```{eval-rst}
.. automodule:: medkit.core.text.operation
    :members: ContextOperation, NEROperation, SegmentationOperation
```

(api:core:text:custom_op)=
### Custom operations

You can also use the following function for instantiating a custom text operation.
The internal class `_CustomTextOperation` is instantiated by this function.

```{eval-rst}
.. autofunction:: medkit.core.text.operation.create_text_operation
.. autoclass:: medkit.core.text.operation.CustomTextOpType
```
