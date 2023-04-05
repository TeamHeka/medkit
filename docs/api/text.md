# Text operation modules

This page lists all components related to text processing.

:::{note}
For more details about all sub-packages, refer to
{mod}`medkit.text`.
:::

## Pre-processing modules

This section provides some information about how to use preprocessing modules.

:::{note}
For more details about public API, refer to
{mod}`medkit.text.preprocessing`.
:::

### Normalizer

If you need to pre-process your document texts for replacing some sub-texts by
other ones, medkit provides a {class}`~.text.preprocessing.Normalizer`
operation to do that and keep span information.

For example, if you want to replace `n°` by `numéro`:

```
from medkit.core.text import TextDocument
from medkit.text.preprocessing import Normalizer, NormalizerRule

doc = TextDocument(text="À l'aide d'une canule n ° 3,")

rule = NormalizerRule(r"n\s*°", "numéro")
op = Normalizer(output_label="preprocessed_text", rules=[rule])
new_segment = op.run([doc.raw_segment])[0]
print(new_segment.text)
```

Results:
* `new_segment.text` : "À l'aide d'une canule numéro 3,"
* `new_segment.spans` : [Span(start=0, end=22),
 ModifiedSpan(length=6, replaced_spans=[Span(start=22, end=25)]),
 Span(start=25, end=28)]


If you want to use some rule-based operations (like
{class}`~.text.ner.RegexpMatcher` for example), document texts may need to be
pre-processed.

For example, concerning the {class}`~.text.ner.RegexpMatcher`:

> When the rule is not sensitive to unicode, we try to convert unicode chars
> to the closest ascii chars. However, some characters need to be pre-processed
> before (e.g., `n°` -> `number`). So, if the text lengths are different, we
> fall back on initial unicode text for detection even if rule is not
> unicode-sensitive.
> In this case, a warning is logged for recommending to pre-process data.

For this use-case, medkit provides some pre-defined rules that you can import
(cf. {mod}`medkit.text.preprocessing`).

For example:
```
from medkit.text.preprocessing import LIGATURE_RULES
```

:::{warning}
If you have a lot of single characters to change, it is not the optimal way to
do it for performance reasons. We plan to provide another operation which will
be faster.
:::

### Other pre-processing modules

medkit also provides an operation for cleaning up text. This module has been
implemented for a specific case of EDS document.

You can follow this [tutorial example](../examples/cleaning_text.md) for more
details about this {class}`~.text.preprocessing.EDSCleaner` module.

## Segmentation modules

This section lists text segmentation modules. They are part of
{mod}`medkit.text.segmentation` package.

:::{note}
For {class}`~.text.segmentation.SectionTokenizer` and
{class}`~.text.segmentation.SyntagmaTokenizer`, you may test an example using :
```
section_tokenizer = SectionTokenizer.get_example()
syntagma_tokenizer = SyntagmaTokenizer.get_example()
```

For {class}`~.text.segmentation.SentenceTokenizer`, you may follow this tutorial
example named [first steps tutorial](../user_guide/first_steps).
:::

:::{note}
For more details about public APIs of each module, refer to
{mod}`medkit.text.segmentation` sub-modules.
:::

## Context detection modules

This section lists text annotators for detecting context. They are part of
{mod}`medkit.text.context` package.

### Hypothesis

If you want to test an example of {class}`~.text.context.HypothesisDetector`,
you may use :
```
detector = HypothesisDetector.get_example()
detector.run(syntagmas)
```

:::{note}
For more details about public APIs, refer to
{mod}`~.text.context.hypothesis_detector`.
:::

### Negation

medkit provides a rule-based negation detector which attaches a negation
attribute to a text segment.

:::{note}
For more details about public APIs, refer to
{mod}`~.text.context.negation_detector`.
:::

### Family reference

medkit provides a rule-based family detector which attaches a family
attribute to a text segment.

:::{note}
For more details about public APIs, refer to
{mod}`~.text.context.family_detector`.
:::

## NER modules

This section lists text annotators for detecting entities. They are part of
{mod}`medkit.text.ner` package.


### Regular Expression Matcher

medkit provides a rule-based entity matcher.

For an example of {class}`~.text.ner.RegexpMatcher` usage, you can follow this
[example tutorial](../user_guide/first_steps.md).

:::{note}
For more details about public APIs, refer to {mod}`~.text.ner.regexp_matcher`.
:::

### IAM system Matcher

The [iamsystem library](https://iamsystem-python.readthedocs.io/en/latest/) is
available under the following medkit operation.

:::{note}
For more details about public APIs, refer to {mod}`~.text.ner.iamsystem_matcher`.
:::

---

medkit also provides a custom implementation ({class}`~.text.ner.MedkitKeyword`) of
[IAM system IEntity](https://iamsystem-python.readthedocs.io/en/latest/getstarted.html#with-a-custom-of-keyword-subclass)
which allows user:
* to associate `kb_name` to `kb_id`
* to provide a medkit entity label (e.g., category) associated to the IAM system entity label (i.e., text to search).


### Quick UMLS Matcher

:::{important}
{class}`~.text.ner.QuickUMLSMatcher` needs additional dependencies that can be installed with `pip
install medkit[quick-umls-matcher]`


QuickUMLSMatcher is a wrapper around 3d-party quickumls.core.QuickUMLS,
which requires a QuickUMLS install to work. A QuickUMLS install can be
created with
```
python -m quickumls.install <umls_installation_path> <destination_path>
```
where <umls_installation_path> is the path to the UMLS folder containing
the MRCONSO.RRF and MRSTY.RRF files.
:::

Given a medkit text document named `doc` with text `The patient has asthma`

```
umls_matcher = QuickUMLSMatcher(version="2021AB", language="ENG")
entities = umls_matcher.run([sentence])
```

The entity (`entities[0]`) will have the following description:
* entity.text = "asthma"
* entity.spans = [Span(16, 22)]
* entity.label = "disorder"

Its normalization attribute (`norm = entity.get_norms()[0]`) will be:
* norm is an instance of {class}`~.text.UMLSNormalization`
* norm.cui = _ASTHMA_CUI
* norm.umls_version = "2021AB"
* norm.term = "asthma"
* norm.score = 1.0
* norm.sem_types = ["T047"]

:::{note}
For more details about public APIs, refer to
{mod}`~.text.ner.quick_umls_matcher`.
:::

### Duckling Matcher

medkit provides an entity annotator that uses [Duckling](https://github.com/facebook/duckling).

Refer to {class}`~.text.ner.DucklingMatcher` for more details about requirements
for using this operation.

:::{note}
For more details about public APIs, refer to
{mod}`~.text.ner.duckling_matcher`.
:::

### Hugging Face Entity Matcher

medkit provides an entity matcher based on Hugging Face models.

:::{important}
{class}`~.text.ner.HFEntityMatcher` needs additional dependencies that can be
installed with `pip install medkit[hf-entity-matcher]`
:::

:::{note}
For more details about public APIs, refer to
{mod}`~.text.ner.hf_entity_matcher`.
:::

### UMLS Coder Normalizer

This operation is not an entity matcher per-say but a normalizer that will
add normalization attributes to pre-existing entities.

:::{important}
{class}`~.text.ner.UMLSCoderNormalizer` needs additional dependencies that can
be installed with `pip install medkit[umls-coder-normalizer]`
:::

:::{note}
For more details about public APIs, refer to
{mod}`~.text.ner.umls_coder_normalizer`.
:::
### UMLS Normalization

This modules provides a subclass of
{class}`~medkit.core.text.normalization.EntityNormalization` to facilitate
the handling of UMLS information.

:::{note}
For more details, refer to {mod}`~.text.ner.umls_normalization`.
:::

(api:text:spacy)=
## Spacy modules

medkit provides operations and utilities for wrapping spacy pipelines into
medkit. They are part of
{mod}`medkit.text.spacy` package.

:::{important}
For using this python module, you need to install [spacy](https://spacy.io/).
These dependencies may be installed with `pip install medkit[spacy]`
:::

## Spacy pipelines

The {class}`~.text.spacy.SpacyPipeline` component is an annotation-level
operation. It takes medkit segments as inputs, runs a spacy pipeline, and
returns medkit segments by converting spacy outputs.

The {class}`~.text.spacy.SpacyDocPipeline` component is a document-level
operation, similarly to {class}`~.core.DocPipeline`.
It takes medkit documents as inputs, runs a spacy pipeline, and
directly attach the spacy annotations to medkit document.

:::{note}
For more info about displacy helpers, refer to {mod}`~.text.spacy.displacy_utils`.
:::

## Translation operations

:::{note}
For translation api, refer to {mod}`~.text.translation`.
:::

### HuggingFace Translator

:::{important}
{class}`.text.translation.HFTranslator` needs additional dependencies that can
be installed with `pip install medkit[hf-translator]`
:::

## Extraction of syntactic relations
This module detects syntactic relations between entities using a parser of
dependencies.

:::{note}
For more info about this module, refer to {mod}`~.text.relations.syntactic_relation_extractor`.
:::
