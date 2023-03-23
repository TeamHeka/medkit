# Large test data

This folder must contain test data used by tests in the `tests/large` directory
but too big to be stored in the git repo, such as model weights.

## `test_pa_speaker_detector.py`:
This test needs:
- a `pyannote/segmentation` directory containing the `pytorch_model.bin` file
from the [pyannote hugging face repo](https://huggingface.co/pyannote/segmentation)
- a `speechbrain/spkrec-ecapa-voxceleb` directory containing the contents of the corresponding
[speechbrain hugging face repo](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb)
