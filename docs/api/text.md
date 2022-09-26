# Text operation modules

This page lists all components related to text processing.

## Pre-processing modules

This section lists non-destructive text preprocessing modules. They are part
of `medkit.text.preprocessing` module.

### Normalizer

```{eval-rst}
.. automodule:: medkit.text.preprocessing.normalizer
    :members:
```

#### Existing rules

:::{note}
You may use some existing normalization rules (`medkit.text.preprocessing.XXX`
for your normalizer:

```{eval-rst}
.. autodata:: medkit.text.preprocessing::LIGATURE_RULES
    :no-value:
```
:::

### Other pre-processing modules

```{eval-rst}
.. automodule:: medkit.text.preprocessing.eds_cleaner
    :members:
```

## Segmentation modules

This section lists text segmentation modules. They are part of
`medkit.text.segmentation` module.

:::{note}
For section and syntagma tokenizers, you may test an example using :
```
section_tokenizer = SectionTokenizer.get_example()
syntagma_tokenizer = SyntagmaTokenizer.get_example()
```

For sentence tokenizer, you have an example in the [first steps tutorial](../user_guide/first_steps)
:::

```{eval-rst}
.. automodule:: medkit.text.segmentation
    :members:
```

## Context detection modules

This section lists text annotators for detecting context. They are part of
`medkit.text.context` module.

### Hypothesis

:::{note}
If you want to test an example of hypothesis detector, you may use :
```
detector = HypothesisDetector.get_example()
detector.run(syntagmas)
```
:::

```{eval-rst}
.. automodule:: medkit.text.context.hypothesis_detector
    :members:
```

### Negation

```{eval-rst}
.. automodule:: medkit.text.context.negation_detector
    :members:
```

### Family reference

```{eval-rst}
.. automodule:: medkit.text.context.family_detector
    :members:
```

## NER modules

This section lists text annotators for detecting entities. They are part of
`medkit.text.ner` module.

### Regular Expression Matcher

```{eval-rst}
.. automodule:: medkit.text.ner.regexp_matcher
    :members:
```

### Quick UMLS Matcher

:::{important}
`QuickUMLSMatcher` needs additional dependencies that can be installed with `pip
install medkit[quick-umls-matcher]`
:::

```{eval-rst}
.. automodule:: medkit.text.ner.quick_umls_matcher
    :members:
```

### Duckling Matcher

```{eval-rst}
.. automodule:: medkit.text.ner.duckling_matcher
    :members:
```

### Hugging Face Entity Matcher

:::{important}
`HFEntityMatcher` needs additional dependencies that can be installed with `pip install medkit[hf-entity-matcher]`
:::

```{eval-rst}
.. automodule:: medkit.text.ner.hf_entity_matcher
    :members:
```

### UMLS Coder Normalizer

This operation is not an entity matcher per-say but a normalizer that will add normalization
attributes to pre-existing entities.

:::{important}
`UMLSCoderNormalizer` needs additional dependencies that can be installed with `pip install medkit[umls-coder-normalizer]`
:::

```{eval-rst}
.. automodule:: medkit.text.ner.umls_coder_normalizer
    :members:
```

## Spacy modules

This section lists operations and utilities related to spacy. They are part of
`medkit.text.spacy` module.
For using this python module, you need to install [spacy](https://spacy.io/).

### Spacy annotation-level pipeline

```{eval-rst}
.. automodule:: medkit.text.spacy.pipeline
    :members:
```

### Spacy document-level pipeline

```{eval-rst}
.. automodule:: medkit.text.spacy.doc_pipeline
    :members:
```

### Displacy helpers

```{eval-rst}
.. automodule:: medkit.text.spacy.displacy_utils
    :members:
```

## Translation operations

This section lists operations related to translation. They are part of
`medkit.text.translation` module.

### HuggingFace Translator

:::{important}
`HFTranslator` needs additional dependencies that can be installed with `pip install medkit[hf-translator]`
:::

```{eval-rst}
.. automodule:: medkit.text.translation
    :members:
```
