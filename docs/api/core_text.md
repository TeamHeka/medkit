# Core text components

This page contains all core text concepts of medkit.

:::{note}
For more details about public APIs, refer to
{mod}`medkit.core.text`.
:::

## Document, Annotations & Attributes

The {class}`~.text.TextDocument` class implements the
{class}`~.core.Document` protocol. It allows to store subclasses of
{class}`~.text.TextAnnotation`, which implements the
{class}`~.core.annotation.Annotation` protocol.


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

{class}`~.text.TextDocument` relies on {class}`~.text.TextAnnotationContainer`,
a subclass of {class}`~.core.AnnotationContainer`, to manage the annotations,

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

### Annotations

For text modality, {class}`~.text.TextDocument` can only contain
{class}`~.text.TextAnnotation`s.

:::{note}
For more details about public APIs, refer to {mod}`medkit.core.text.annotation`).
:::

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

:::{note}
Each text annotation class inherits from the common interfaces provided by the
core component (cf. [Annotation](api:core:annotation))
:::

### Attributes

Text annotations can receive attributes, which will be instances of the core
{class}`~.core.Attribute` class.

Among attributes, {mod}`medkit.core.text` proposes
{class}`~medkit.core.text.entity_norm_attribute.EntityNormAttribute`, to be used
for normalization attributes, in order to have a common structure for
normalization information, independently of the operation used to create it.


(api:core-text:span)=
## Spans

medkit relies on the concept of spans for following all text modifications
made by the different operations.

:::{note}
For more details about public APIs, refer to
{mod}`medkit.core.text.span`.
:::

medkit also proposes a set of utilities for manipulating these spans if we need
it when implementing a new medkit operation.

:::{note}
For more details about public APIs, refer to  {mod}`medkit.core.text.span_utils`.
:::

:::{seealso}
You may also take a look to the [spans notebook example](../examples/spans).
:::


## Text utilities

These utilities have some preconfigured patterns for preprocessing text documents without destruction. They are not really supposed to be used directly, but rather inside a cleaning operation.

:::{note}
For more details about public APIs, refer to {mod}`medkit.core.text.utils`.
:::

:::{seealso}
 Medkit provides the {class}`~medkit.text.preprocessing.eds_cleaner.EDSCleaner` class that combines all these utilities to clean french documents (related to EDS documents coming from PDF).
:::


## Operations

Abstract subclasses of {class}`~.core.Operation` have been defined for text
to ease the development of text operations according to `run` operations.


```{eval-rst}
.. autoclasstree:: medkit.core.operation medkit.core.text.operation
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Operation hierarchy
```

:::{note}
For more details about public APIs, refer to {mod}`medkit.core.text.operation`.
:::

Internal class `_CustomTextOperation` has been implemented to allow user to
call {func}`~.text.create_text_operation` for easily instantiating a custom
text operation.

:::{seealso}
You may refer to this [tutorial](../examples/custom_text_operation) as example
of definition of custom operation.
:::
