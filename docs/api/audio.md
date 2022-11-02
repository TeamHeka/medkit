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

`DocTranscriber` is the operation handling the transformation of `AudioDocument`
instances into `TranscribedDocument` instances (subclas of `TextDocument`). The
actual conversion from text to audio is delegated to components complying with
the `TranscriberFunction` protocol. `HFTranscriberFunction` and
`SBTranscriberFunction` are implementations of `TranscriberFunction`, allowing
to use HuggingFace transformer models and speechbrain models respectively.

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

### HFTranscriberFunction

```{important}
`HFTranscriberFunction` needs additional dependencies that can be installed with
`pip install medkit[hf-transcriber-function]`
```

```{eval-rst}
.. automodule:: medkit.audio.transcription.hf_transcriber_function
    :members:
```

### SBTranscriberFunction

```{important}
`SBTranscriberFunction` needs additional dependencies that can be installed with
`pip install medkit[sb-transcriber-function]`
```

```{eval-rst}
.. automodule:: medkit.audio.transcription.sb_transcriber_function
    :members:
```
