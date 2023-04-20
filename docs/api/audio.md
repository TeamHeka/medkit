# Audio operations

This page lists all components related to audio processing.

:::{note}
For more details about all sub-packages, refer to
{mod}`medkit.audio`.
:::

## Pre-processing operations

This section provides some information about how to use preprocessing modules
for audio.

:::{note}
For more details about public APIs, refer to {mod}`medkit.audio.preprocessing`.
:::

### Downmixer

For more details, refer to {mod}`medkit.audio.preprocessing.downmixer`.

### Power normalizer

For more details, refer to {mod}`medkit.audio.preprocessing.power_normalizer`.

### Resampler

:::{important}
{class}`~.audio.preprocessing.Resampler` needs additional dependencies that can
be installed with `pip install medkit-lib[resampler]`
:::

For more details, refer to {mod}`medkit.audio.preprocessing.resampler`.

## Segmentation operations

This section lists audio segmentation operations. They are part of the
{mod}`medkit.audio.segmentation` module.


### WebRTC voice detector

For more details, refer to
{mod}`medkit.audio.segmentation.webrtc_voice_detector`.

### Pyannote speaker detector

:::{important}
{class}`~.audio.segmentation.PASpeakerDetector` needs additional dependencies
that can be installed with `pip install medkit-lib[pa-speaker-detector]`
:::

For more details, refer to {mod}`medkit.audio.segmentation.pa_speaker_detector`.

## Audio Transcription

This section lists operations and other components to use to perform audio
transcription.
They are part of the {mod}`medkit.audio.transcription` module.

{class}`~.audio.transcription.DocTranscriber` is the operation handling the
transformation of {class}`~.core.audio.AudioDocument` instances into
{class}`~.audio.transcription.TranscribedDocument` instances (subclass of
{class}`~.core.text.TextDocument`).

The actual conversion from text to audio is delegated to components complying
with the {class}`~.audio.transcription.TranscriberFunction` protocol.
{class}`~.audio.transcription.HFTranscriberFunction` and
{class}`~.audio.transcription.SBTranscriberFunction` are implementations of
{class}`~.audio.transcription.TranscriberFunction`, allowing to use HuggingFace
transformer models and speechbrain models respectively.

### DocTranscriber

For more details, refer to {mod}`medkit.audio.transcription.doc_transcriber`.

### TranscribedDocument

For more details, refer to {mod}`medkit.audio.transcription.transcribed_document`.

### HFTranscriberFunction

:::{important}
{class}`~.audio.transcription.HFTranscriberFunction` needs additional
dependencies that can be installed with 
`pip install medkit-lib[hf-transcriber-function]`
:::

For more details, refer to
{mod}`medkit.audio.transcription.hf_transcriber_function`.

### SBTranscriberFunction

:::{important}
{class}`~.audio.transcription.SBTranscriberFunction` needs additional
dependencies that can be installed with
`pip install medkit-lib[sb-transcriber-function]`
:::

For more details, refer to
{mod}`medkit.audio.transcription.sb_transcriber_function`.
