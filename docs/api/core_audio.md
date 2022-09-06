# Core audio classes

This page contains all core audio concepts of medkit.

## Document & Annotations

The `AudioDocument` class derives the `Document` and allows it to store
subclasses of `AudioAnnotation`.

```{eval-rst}
.. autoclasstree:: medkit.core.document medkit.core.audio.document
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Document hierarchy
```

```{eval-rst}
.. autoclasstree:: medkit.core.annotation medkit.core.audio.annotation
    :strict:
    :namespace: medkit.core
    :align: center
    :caption: Audio Annotation hierarchy
```

```{eval-rst}
.. automodule:: medkit.core.audio.document
    :members:
    :inherited-members:
```

```{eval-rst}
.. automodule:: medkit.core.audio.annotation
    :members:
    :inherited-members:
```

## Span

Similary to [text spans](api:core-text:span), audio annotations have an audio span pointing to the part of
the audio document that is annotated. Contrary to text annotations, multiple discontinous spans are not supported. An audio annotation can only have 1 continuous span, and there is no concept of "modified spans".

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
