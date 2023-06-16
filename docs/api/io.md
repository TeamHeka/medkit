# I/O components

This page lists all components for converting and loading/saving data.

:::{note}
For more details about public APIs, refer to
{mod}`medkit.io`.
:::

(api:io:brat)=
## Brat

Brat is a web-based tool for text annotation. Medkit supports the input and output conversion of text documents. 

:::{seealso}
For more details, refer to {mod}`medkit.io.brat`.
You may refer to this [example](../examples/brat_io.md) for more information.
:::


## Doccano

Doccano is a text annotation tool, you can import doccano files coming from these tasks:

* Relation extraction: named entity recognition with relations
* Sequence labeling: named entity recognition without relations
* Text classification: A document with a category

Supported tasks can be found in {class}`medkit.io.doccano.DoccanoTask`. You can load documents from a JSONL file or a zip file directory.

For more details, refer to {mod}`medkit.io.doccano`.

(api:io:spacy)=
## Spacy

:::{important}
For using spacy converters, you need to install [spacy](https://spacy.io/).
These dependencies may be installed with `pip install medkit-lib[spacy]`
:::

:::{seealso}
You may refer to this [example](../examples/spacy_io.md) for more information.
:::

For more details, refer to {mod}`medkit.io.spacy`.

## medkit-json

medkit has some utilities to export and import medkit documents to json format.

You can use {mod}`medkit.io.medkit_json.save_text_documents` to save a list of documents, and then {mod}`medkit.io.medkit_json.load_text_documents` to load them in medkit.

For more details, refer to {mod}`medkit.io.medkit_json`.

## RTTM

Rich Transcription Time Marked (.rttm) files contains diarization information. 
Medkit supports input and output conversion of audio documents.

For more details, refer to {mod}`medkit.io.rttm`.
