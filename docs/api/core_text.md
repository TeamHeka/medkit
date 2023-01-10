# Core text classes

This page contains all core text concepts of medkit.

## Document & Annotations

The `TextDocument` class derives the `Document` and allows it to store
subclasses of `TextAnnotation`.

```{eval-rst}
.. autoclasstree:: medkit.core.document medkit.core.text.document
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Document hierarchy
```

```{eval-rst}
.. autoclasstree:: medkit.core.annotation medkit.core.text.annotation
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Text Annotation hierarchy
```

```{eval-rst}
.. automodule:: medkit.core.text.document
    :members:
    :inherited-members:
```

```{eval-rst}
.. automodule:: medkit.core.text.annotation
    :members:
    :inherited-members:
```

```{eval-rst}
.. automodule:: medkit.core.text.normalization
    :members:
    :inherited-members:
```

(api:core-text:span)=
## Span (specific to text)

```{eval-rst}
.. autoclass:: medkit.core.text::Span
```

```{eval-rst}
.. autoclass:: medkit.core.text::ModifiedSpan
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
    :members:
```
