# Audio operations

This page lists all components related to audio processing.

## Pre-processing operations

This section lists audio preprocessing operations. They are part
of the `medkit.audio.preprocessing` module.

### Downmixer

```{eval-rst}
.. automodule:: medkit.audio.preprocessing.downmixer
    :members:
```

### Power normalizer

```{eval-rst}
.. automodule:: medkit.audio.preprocessing.power_normalizer
    :members:
```

### Resampler

```{important}
`Resampler` needs additional dependencies that can be installed with `pip install medkit[resampler]`
```

```{eval-rst}
.. automodule:: medkit.audio.preprocessing.resampler
    :members:
```

## Segmentation operations

This section lists audio segmentation operations. They are part of the
`medkit.audio.segmentation` module.


### WebRTC voice detector

```{eval-rst}
.. automodule:: medkit.audio.segmentation.webrtc_voice_detector
    :members:
```

## Audio Transcription

This section lists operations and other components to use to perform audio transcription.
They are part of the `medkit.audio.transcription` module.

`DocTranscriber` is the operation handling the transformation of `AudioDocument` instances
into `TranscribedDocument` instances (subclas of `TextDocument`). The actual conversion from text to audio is delegated to components complying with the `AudioTranscriber` protocol. `HFTranscriber` is such an implementation of `AudioTranscriber`, using a HuggingFace transformer model.

### DocTranscriber

```{eval-rst}
.. automodule:: medkit.audio.transcription.doc_transcriber
    :members:
```

### TranscribedDocument

```{eval-rst}
.. automodule:: medkit.audio.transcription.transcribed_document
    :members:
```

### HFTranscriber

```{important}
`HFTranscriber` needs additional dependencies that can be installed with `pip install medkit[hf-transcriber]`
```

```{eval-rst}
.. automodule:: medkit.audio.transcription.hf_transcriber
    :members:
```

### SBTranscriber

```{important}
`SBTranscriber` needs additional dependencies that can be installed with `pip install medkit[sb-transcriber]`
```

```{eval-rst}
.. automodule:: medkit.audio.transcription.sb_transcriber
    :members:
```
