---
jupytext:
    formats: md:myst
    text_representation:
        extension: .md
        format_name: myst
        format_version: 0.13
        jupytext_version: 1.13.8
kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---
# Using pipelines

This tutorial will show you how to encapsulate operations into a pipeline,
and how to create pipelines to augment documents.

## Using operations without a pipeline

Let's start by instantiating the preprocessing, segmentation, context detection
and entity recognition operations that we want to use. We are simply going to
reuse the ones from the [First steps](first_steps.md) tutorial:

```{code-cell} ipython3
from medkit.text.preprocessing import RegexpReplacer
from medkit.text.segmentation import SentenceTokenizer, SyntagmaTokenizer
from medkit.text.context import NegationDetector, NegationDetectorRule
from medkit.text.ner import RegexpMatcher, RegexpMatcherRule

# preprocessing
rule = (r"(?<=\d)\.(?=\d)", ",")
normalizer = RegexpReplacer(output_label="clean_text", rules=[rule])

# segmentation
sent_tokenizer = SentenceTokenizer(
    output_label="sentence",
    punct_chars=[".", "?", "!", "\n"],
)

synt_tokenizer = SyntagmaTokenizer(
    output_label="syntagma",
    separators=[r"\bmais\b", r"\bet\b"],
)

# context detection 
neg_rules = [
    NegationDetectorRule(regexp=r"\bpas\s*d[' e]\b"),
    NegationDetectorRule(regexp=r"\bsans\b", exclusion_regexps=[r"\bsans\s*doute\b"]),
    NegationDetectorRule(regexp=r"\bne\s*semble\s*pas"),
]
neg_detector = NegationDetector(output_label="is_negated", rules=neg_rules)

# entity recognition
regexp_rules = [
    RegexpMatcherRule(regexp=r"\ballergies?\b", label="problem"),
    RegexpMatcherRule(regexp=r"\basthme\b", label="problem"),
    RegexpMatcherRule(regexp=r"\ballegra?\b", label="treatment", case_sensitive=False),
    RegexpMatcherRule(regexp=r"\bvaporisateurs?\b", label="treatment"),
    RegexpMatcherRule(regexp=r"\bloratadine?\b", label="treatment", case_sensitive=False),
    RegexpMatcherRule(regexp=r"\bnasonex?\b", label="treatment", case_sensitive=False),
]
regexp_matcher = RegexpMatcher(rules=regexp_rules, attrs_to_copy=["is_negated"])
```

Each of these operations has a `run()` method, which we could call sequentially,
passing along the output from one operation as the input to the next operation,
and using a document's raw text segment as the initial input:


```{code-cell} ipython3
from pathlib import Path
from medkit.core.text import TextDocument

text_file = Path("../data/text/1.txt")
# You can download the file available in source code
# !wget https://raw.githubusercontent.com/TeamHeka/medkit/main/docs/data/text/1.txt
# or create your file and copy the text
doc = TextDocument(text=text_file.read_text(encoding="utf-8"))

# clean_segments contains only 1 segment: the preprocessed full text segment
clean_segments = normalizer.run([doc.raw_segment])
sentences = sent_tokenizer.run(clean_segments)
syntagmas = synt_tokenizer.run(sentences)
# the negation detector doesn't return new annotations
# but rather appends attributes to the segments it received
neg_detector.run(syntagmas)
entities = regexp_matcher.run(syntagmas)
```

But it is also possible to wrap all this operations into a `Pipeline` object,
that will be responsible of calling the `run()` method of each operation, with
the appropriate input annotations.

## Why use a pipeline?

What are the advantages of using pipelines instead of just directly calling each
operations as we just did?

In this particular case, they aren't any real advantages. Because this is a
tutorial and we want to keep things simple, there aren't so many operations and
they are called in a linear fashion. But in real life the chaining of operations
could be more complex and then it could be easier to do that through a pipeline.

Also, pipelines are composable (each pipeline is an operation that can itself be
put into another pipeline), therefore they can be used to structure complex
flows into smaller units handling a subpart of the processing. This also makes
it possible to reuse a pipeline for different projects, for instance by
regrouping common preprocessing steps.

If you are interested in [provenance tracing](provenance.md) (knowing how each
annotation was generated), then it can also be easier to handle that with a
pipeline.

Finally, in the future of medkit the scope of pipelines might be expanded to
handle more things such as batching, parallelization, and maybe training of
trainable components.

## Constructing a pipeline

Despite its name, a pipeline doesn't have to be linear. Operations can be
connected in more complex ways, making the pipeline something closer to a
dataflow graph. We have to describe how operations are connected to each others,
and this is done through {class}`~medkit.core.PipelineStep` objects. Let's do
that for our use case: 

```{code-cell} ipython3
from medkit.core import PipelineStep

pipeline_steps = [
    PipelineStep(normalizer, input_keys=["full_text"], output_keys=["clean_text"]),
    PipelineStep(sent_tokenizer, input_keys=["clean_text"], output_keys=["sentences"]),
    PipelineStep(synt_tokenizer, input_keys=["sentences"], output_keys=["syntagmas"]),
    PipelineStep(neg_detector, input_keys=["syntagmas"], output_keys=[]),  # no output
    PipelineStep(regexp_matcher, input_keys=["syntagmas"], output_keys=["entities"]),
]
```

Each `PipelineStep` associates an operation with "keys". As we just said, the
pipeline can be seen as a graph in which operations have to be connected to each
other, and the "keys" are just names we put on these connections to make it
easier to describe them. The steps we just constructed can be represented like
this:

```{mermaid}
:align: center
graph LR
    A((?))
    B(normalizer)
    C(sent_tokenizer)
    D(synt_tokenizer)
    E(neg_detector)
    F(entity_matcher)
    G((?)):::io

    A -- full_text --> B
    B -- clean_text --> C
    C -- sentences --> D
    D -- syntagmas --> E
    D -- syntagmas --> F
    F -- entities --> G

    classDef io fill:#fff4dd,stroke:#edb:
```

It might be surprising to see the negation detector on the same level as the
entity matcher. This is because the negation detector takes the syntagmas as
input, just like the entity matcher, but it has no output (it modifies the
syntagmas in-place by adding attributes to them).

However, for our pipeline to function correctly, we do need the negation
detector to be run before the entity matcher, since the entity matcher must copy
the negation attributes onto the new entities (if this is unclear to you, make
sure you have read the [First steps tutorial](first_steps.md)). The pipeline
steps will simply be run in the order they were given, so we are safe here.

If we take another look at the graph, we notice 2 question-mark vertices:
 - the first one, connected to the normalizer via the `"full_text"` key,
   represents the source of the segments that will be fed into the normalizer,
   still unknown at this point since they are not the product of previous
   operation;
 - the second one, connected to the entity matcher via the `"entities"` key,
   represents the destination of the entities produced by the matcher, also
   still unknown for now.

We will now use the our pipeline steps to create a
{class}`~medkit.core.Pipeline` object:

```{code-cell} ipython3
from medkit.core import Pipeline

pipeline = Pipeline(pipeline_steps, input_keys=["full_text"], output_keys=["entities"])
```

In addition to the steps, we provide the pipeline with 2 arguments:
 - `input_keys=["full_text"]` tells the pipeline that the first argument passed
   to its `run()` method corresponds to the `"full_text"` key, and therefore
   should be fed as input to the normalizer;
 - `output_keys=["entities"]` tells the pipeline that the first (and unique)
   return value of its `run()` method correspond to the `"entities"` key, and
   therefore that it should be the output of the entity matcher.

Note that for our use case, the pipeline only has one input and one output, but
creating more complex pipelines with multiple input arguments and multiple
return values is supported.

Let's run our pipeline and make sure everything is ok:

```{code-cell} ipython3
entities = pipeline.run([doc.raw_segment])
for entity in entities:
    neg_attr = entity.attrs.get(label="is_negated")[0]
    print(f"text='{entity.text}', label={entity.label}, is_negated={neg_attr.value}")
```

Seems good!

## Composing pipelines

Let's complicate a little bit our use case by adding a new operation to detect
hypothesis, using the
{class}`~medkit.text.context.hypothesis_detector.HypothesisDetector` class. Just
like `NegationDetector`, `HypothesisDetector` is a regex-based component that is
configured through rules and that adds attributes to pre-existing entities or
segments.

```{code-cell} ipython3
from medkit.text.context import HypothesisDetector, HypothesisDetectorRule

hyp_rules = [
    HypothesisDetectorRule(regexp=r"\bsi\b"),
    HypothesisDetectorRule(regexp=r"\bpense\b"),
    HypothesisDetectorRule(regexp=r"\semble\b"),
]
hyp_detector = HypothesisDetector(output_label="is_hypothesis", rules=hyp_rules)
```

We could just insert the hypothesis detector in the list of steps and
re-instantiate a new `Pipeline`. But our pipeline is becoming a little too big
and complicated to our taste, so instead we will regroup some of the operations
into sub-pipelines.

In particular, we group together the sentence and syntagmas tokenizers into a
tokenization sub-pipeline, taking a full text as input and returning syntagmas:

```{code-cell} ipython3
tok_steps = [
    PipelineStep(sent_tokenizer, input_keys=["full_text"], output_keys=["sentences"]),
    PipelineStep(synt_tokenizer, input_keys=["sentences"], output_keys=["syntagmas"]),
]
tok_pipeline = Pipeline(tok_steps, input_keys=["full_text"], output_keys=["syntagmas"])
```

and we wrap the negation and hypothesis detectors into a context detection
pipeline, taking syntagmas as input and adding negation and hypothesis attribute
to them:

```{code-cell} ipython3
context_steps = [
    PipelineStep(neg_detector, input_keys=["syntagmas"], output_keys=[]),
    PipelineStep(hyp_detector, input_keys=["syntagmas"], output_keys=[]),
]
context_pipeline = Pipeline(context_steps, input_keys=["syntagmas"], output_keys=[])
```

As mentioned earlier, pipelines are operations: they have a `run()` method that
take input data and returns newly produced data when appropriate. So they can
also be put in a pipeline, like any operation. Let's do that to rebuild our main
pipeline:

```{code-cell} ipython3
pipeline_steps = [
    PipelineStep(
        normalizer,
        input_keys=["full_text"],
        output_keys=["clean_text"],
    ),
    PipelineStep(
        tok_pipeline,
        input_keys=["clean_text"],
        output_keys=["syntagmas"],
    ),
    PipelineStep(
        context_pipeline,
        input_keys=["syntagmas"],
        output_keys=[],
    ),
    PipelineStep(
        regexp_matcher, 
        input_keys=["syntagmas"], 
        output_keys=["entities"],
    ),
]
pipeline = Pipeline(pipeline_steps, input_keys=["full_text"], output_keys=["entities"])
```

## Using a document pipeline

The pipeline we have created can be seen as an "annotation-level" pipeline. It
takes {class}`~medkit.core.text.Segment` objects as input and returns
{class}`~medkit.core.text.Entity` objects (`Segment` and `Entity` both being
subclasses of {class}`~medkit.core.text.TextAnnotation`).

When using it to annotate several documents, we would typically write something
like:

```{code-cell} ipython3
# You can download the files available in source code
# !wget https://raw.githubusercontent.com/TeamHeka/medkit/main/docs/data/text/1.txt
# !wget https://raw.githubusercontent.com/TeamHeka/medkit/main/docs/data/text/2.txt

def load_docs():
    text_files = [Path("../data/text/1.txt"), Path("../data/text/2.txt")]
    return [TextDocument(text=f.read_text(encoding="utf-8")) for f in text_files]

docs = load_docs()

for doc in docs:
    entities = pipeline.run([doc.raw_segment])
    for entity in entities:
        doc.anns.add(entity)
```

To handle this common use case, medkit provides a
{class}`~medkit.core.DocPipeline` class. This is how we would use it:

```{code-cell} ipython3
from medkit.core import DocPipeline

doc_pipeline = DocPipeline(pipeline=pipeline)

docs = load_docs()
doc_pipeline.run(docs)
```

## Wrapping it up

In this tutorial, we have learnt how to instantiate a `Pipeline` and describe
how operations are connected with each others through `PipelineStep` objects. We
have also seen how sub-pipelines can be nested into other pipelines. Finally, we
have seen how to transform an annotation-level `Pipeline` into a document-level
`DocPipeline`.

If you have more questions about pipelines or wonder how to build more complex
flows, you may want to take a look at the [pipeline API
docs](api:core:pipeline). If you are interested in the advantages of pipelines
as regard provenance tracing, you may read the [provenance tracing tutorial](provenance.md).
