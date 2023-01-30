# Core audio classes

This page contains all core audio concepts of medkit.

## Document & Annotations

The {class}`~medkit.core.text.document.AudioDocument` class implements the
{class}`~medkit.core.Document` protocol. It allows to store instances of the
{class}`~medkit.core.audio.annotation.Segment` class, which implements the
{class}`~medkit.core.Annotation` protocol.

`AudioDocument` relies on {class}`~medkit.core.text.document.AudioAnnotationContainer`, a
subclass of {class}`~medkit.core.AnnotationContainer`, to store the annotations,

```{mermaid}
:align: center
:caption: Audio document and annotation hierarchy

classDiagram
    direction TD
    class AudioDocument{
        uid: str
        anns: AudioAnnotationContainer
    }
    class AudioAnnotationContainer{
    }
    class Segment{
        <<abstract>>
        uid: str
        label: str
        attrs: AttributeContainer
    }
    AudioDocument *-- AudioAnnotationContainer
    AudioAnnotationContainer o-- AudioAnnotation
```

### Document

```{eval-rst}
.. automodule:: medkit.core.audio.document
    :members:
    :inherited-members:
```

### Annotations

```{eval-rst}
.. automodule:: medkit.core.audio.annotation
    :members:
    :inherited-members:
```

## Span

Similary to [text spans](api:core-text:span), audio annotations have an audio span pointing to the part of
the audio document that is annotated. Contrary to text annotations, multiple discontinuous spans are not supported. An audio annotation can only have 1 continuous span, and there is no concept of "modified spans".

```{eval-rst}
.. automodule:: medkit.core.audio.span
    :members:
```

## Audio Buffer

Access to the actual waveform data is handled through `AudioBuffer` instances. The same way text annotations
store the text they refer to in their `text` property, which holds a string, audio annotations store the portion of the audio signal they refer to in an `audio` property holding an `AudioBuffer`.

The contents of an `AudioBuffer` might be different from the intial raw signal if it has been preprocessed. If
the signal is identical to the initial raw signal, then a `FileAudioBuffer` can be used (with appropriate `start` and `end` boundaries). Otherwise, a `MemoryAudioBuffer` has to be used as there is no corresponding audio file containing the signal.

Creating a new `AudioBuffer` containing a portion of a pre-existing buffer is done through the `trim()` method.

```{eval-rst}
.. automodule:: medkit.core.audio.audio_buffer
    :members:
```

## Operations

Abstract sub-classes of `Operation` have been defined for audio to ease the
development of audio operations according to `run` operations.

```{eval-rst}
.. automodule:: medkit.core.audio.operation
    :members:
```
