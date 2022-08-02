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

# Demo

## Basic example with some operations

(get_data)=
### Get data

```{code-cell} ipython3
from pathlib import Path
from pprint import pprint

from medkit.core.text import TextDocument

current_dir = Path('.').resolve()
input_dir = current_dir / "input" / "demo"
output_dir = current_dir / "_out" / "demo"

# load docs
docs = []
for filename in ["1.txt", "2.txt"]:
    with open(input_dir / filename) as f:
        docs.append(TextDocument(text=f.read()))

for index, doc in enumerate(docs):
  print(f"Document {index} : {doc.text}")
```

(cfg_op)=
### Init and configure operations

For this example, we use the following operations:
* unicode normalizer
* sentence tokenizer
* negation detector
* regexp matcher with some pre-defined rules

```{code-cell} ipython3
from medkit.text.preprocessing import Normalizer, LIGATURE_RULES
from medkit.text.segmentation import SentenceTokenizer
from medkit.text.ner import RegexpMatcher
from medkit.text.context import NegationDetector

unicode_normalizer = Normalizer(output_label="text-wo-ligatures", rules=LIGATURE_RULES)
sentence_tokenizer = SentenceTokenizer()
negation_detector = NegationDetector(output_label="negation")

rules_file = input_dir / "regexp_matcher_rules.yml" 
regexp_matcher_rules = RegexpMatcher.load_rules(rules_file)
regexp_matcher = RegexpMatcher(rules=regexp_matcher_rules, attrs_to_copy=["negation"])
```

Here is an example of regexp matcher rules used in this case:

```{code-cell} ipython3
with open(rules_file, 'r') as f:
  print(f.read())
```

### Annotate each document

```{code-cell} ipython3
for doc in docs:
    anns = [doc.raw_segment]
    anns = unicode_normalizer.run(anns)
    anns = sentence_tokenizer.run(anns)
    negation_detector.run(anns)
    anns = regexp_matcher.run(anns)
    for ann in anns:
        doc.add_annotation(ann)
```

(results)=
### Visualize results

The document has been augmented with entities detected by the regexp matcher.

Here is a visual representation of entities detected on document 1.txt.

```{code-cell} ipython3
from spacy import displacy

doc = docs[0]

ex = [{
        "text": doc.text,
        "ents": [{"start": ann.spans[0].start, 
                  "end": ann.spans[-1].end, 
                  "label": ann.label } for ann in doc.get_annotations()],
}]
displacy.render(ex, style="ent", manual="True")
```

Here is the representation of the full document data

```{code-cell} ipython3
doc = docs[0]
data = doc.to_dict()
pprint(data)
```

## Pipeline example

### Get data

cf. [Get data](get_data)

### Init and configure operations

cf. [Init and configure operations](cfg_op)

### Configure pipeline

```{code-cell} ipython3
from medkit.core import Pipeline, PipelineStep

steps = [
    PipelineStep(
        unicode_normalizer, input_keys=["full_text"], output_keys=["norm_text"]
    ),
    PipelineStep(
        sentence_tokenizer, input_keys=["norm_text"], output_keys=["sentences"]
    ),
    PipelineStep(negation_detector, input_keys=["sentences"], output_keys=[]),
    PipelineStep(regexp_matcher, input_keys=["sentences"], output_keys=["entities"]),
]
pipeline = Pipeline(steps, input_keys=["full_text"], output_keys=["entities"])
```

### Run annotation pipeline on each document

```{code-cell} ipython3
for doc in docs:
    full_text_anns = [doc.raw_segment]
    entities = pipeline.run(full_text_anns)
    # annotate doc with results
    for entity in entities:
        doc.add_annotation(entity)
```

### Visualize results

The document has been augmented with entities detected by the regexp matcher.
(cf. [Visualize results](results))


With pipeline, you may also visualise a category of annotations using the 
pipeline output key (e.g., 'entities') :

```{code-cell} ipython3
from spacy import displacy

doc = docs[0]

ex = [{
        "text": doc.text,
        "ents": [{
            "start": entity.spans[0].start, 
            "end": entity.spans[-1].end, 
            "label": entity.label}
            for entity in doc.get_annotations_by_key(key="entities")],
}]
displacy.render(ex, style="ent", manual="True")
```

## Pipeline example with provenance

### Initialize store and provenance tracing

```{code-cell} ipython3
from medkit.core import DictStore, ProvTracer

store = DictStore()
prov_tracer = ProvTracer(store)
```

### Get data

```{code-cell} ipython3
from pathlib import Path
from pprint import pprint

from medkit.core.text import TextDocument

current_dir = Path('.').resolve()
input_dir = current_dir / "input" / "demo"

# load docs
docs = []
for filename in ["1.txt", "2.txt"]:
    with open(input_dir / filename) as f:
        docs.append(TextDocument(text=f.read(), store=store))

for index, doc in enumerate(docs):
  print(f"Document {index} : {doc.text}")
```

### Init and configure operations

cf. [Init and configure operations](cfg_op)

### Configure pipeline

```{code-cell} ipython3
from medkit.core import Pipeline, PipelineStep

steps = [
    PipelineStep(
        unicode_normalizer, input_keys=["full_text"], output_keys=["norm_text"]
    ),
    PipelineStep(
        sentence_tokenizer, input_keys=["norm_text"], output_keys=["sentences"]
    ),
    PipelineStep(negation_detector, input_keys=["sentences"], output_keys=[]),
    PipelineStep(regexp_matcher, input_keys=["sentences"], output_keys=["entities"]),
]
pipeline = Pipeline(steps, input_keys=["full_text"], output_keys=["entities"])
```

```{warning}
Do not forget to enable provenance tracing for the pipeline.
```

```{code-cell} ipython3
pipeline.set_prov_tracer(prov_tracer)
```

### Run annotation pipeline on each document

```{code-cell} ipython3
for doc in docs:
    full_text_anns = [doc.raw_segment]
    entities = pipeline.run(full_text_anns)
    # annotate doc with results
    for entity in entities:
        doc.add_annotation(entity)
```

### Visualize results

The document has been augmented with entities detected by the regexp matcher.
(cf. [Visualize results](results))

```{code-cell} ipython3
import os

from medkit.core.text import TextAnnotation
from medkit.tools import save_prov_to_dot

os.makedirs(output_dir, exist_ok=True)
dot_graph = output_dir / "prov.dot"

# save provenance to dot file
# (generate pgn with dot -Tpng prov.dot -o prov.png)
save_prov_to_dot(
    prov_tracer,
    dot_graph,
)
```

```{code-cell} ipython3
cmd = f"dot -Tpng {output_dir}/prov.dot -o {output_dir}/prov.png"
os.system(cmd)

png_file = output_dir / "prov.png"
```

```{code-cell} ipython3
from IPython.display import Image
Image(png_file)
```

## Pipeline example with different provenance granularity

### Initialize store and provenance tracing

```{code-cell} ipython3
from medkit.core import DictStore, ProvTracer

store = DictStore()
prov_tracer = ProvTracer(store)
```

### Get data

```{code-cell} ipython3
from pathlib import Path
from pprint import pprint

from medkit.core.text import TextDocument

current_dir = Path('.').resolve()
input_dir = current_dir / "input" / "demo"

# load docs
docs = []
for filename in ["1.txt", "2.txt"]:
    with open(input_dir / filename) as f:
        docs.append(TextDocument(text=f.read(), store=store))

for index, doc in enumerate(docs):
  print(f"Document {index} : {doc.text}")
```

### Define a sub-pipeline

```{code-cell} ipython3
class ContextPipeline(Pipeline):
    def __init__(self):
        unicode_normalizer = Normalizer(output_label="text-wo-ligatures", rules=LIGATURE_RULES)
        sentence_tokenizer = SentenceTokenizer()
        negation_detector = NegationDetector(output_label="negation")
        steps = [
            PipelineStep(
                unicode_normalizer, input_keys=["full_text"], output_keys=["norm_text"]
            ),
            PipelineStep(
                sentence_tokenizer, input_keys=["norm_text"], output_keys=["sentences"]
            ),
            PipelineStep(negation_detector, input_keys=["sentences"], output_keys=[]),
        ]
        super().__init__(steps, input_keys=["full_text"], output_keys=["sentences"])
```

### Init and configure operations

```{code-cell} ipython3
context_pipeline = ContextPipeline()
regexp_matcher_rules = RegexpMatcher.load_rules(
    input_dir / "regexp_matcher_rules.yml"
)
regexp_matcher = RegexpMatcher(rules=regexp_matcher_rules, attrs_to_copy=["negation"])
```

### Configure main pipeline

```{code-cell} ipython3
from medkit.core import Pipeline, PipelineStep

steps = [
    PipelineStep(
        context_pipeline,
        input_keys=["full_text"],
        output_keys=["sentences_with_context"],
    ),
    PipelineStep(
        regexp_matcher,
        input_keys=["sentences_with_context"],
        output_keys=["entities"],
    ),
]

pipeline = Pipeline(steps, input_keys=["full_text"], output_keys=["entities"])
```

```{warning}
Do not forget to enable provenance tracing for the pipeline.
```

```{code-cell} ipython3
pipeline.set_prov_tracer(prov_tracer)
```

### Run annotation pipeline on each document

```{code-cell} ipython3
for doc in docs:
    full_text_anns = [doc.raw_segment]
    entities = pipeline.run(full_text_anns)
    # annotate doc with results
    for entity in entities:
        doc.add_annotation(entity)
```

### Visualize results

The document has been augmented with entities detected by the regexp matcher.
(cf. [Visualize results](results))

Provenance information may be visualized at different levels:

```{code-cell} ipython3
import os

from medkit.core.text import TextAnnotation
from medkit.tools import save_prov_to_dot

os.makedirs(output_dir, exist_ok=True)
```

#### Basic information (graph depth = 0)

```{code-cell} ipython3
dot_graph = output_dir / "prov.dot"
png_graph = output_dir / "prov.png"

# save provenance to dot file
# (generate pgn with dot -Tpng prov.dot -o prov.png)
save_prov_to_dot(
    prov_tracer,
    dot_graph,
    max_sub_prov_depth=0,
)

cmd = f"dot -Tpng {dot_graph} -o {png_graph}"
os.system(cmd)

from IPython.display import Image
Image(png_graph)
```

#### Intermediate information (graph depth = 1)

```{code-cell} ipython3
dot_graph = output_dir / "prov_intermediate.dot"
png_graph = output_dir / "prov_intermediate.png"

# save provenance to dot file
# (generate pgn with dot -Tpng prov.dot -o prov.png)
save_prov_to_dot(
    prov_tracer,
    dot_graph,
    max_sub_prov_depth=1,
)

cmd = f"dot -Tpng {dot_graph} -o {png_graph}"
os.system(cmd)

from IPython.display import Image
Image(png_graph)
```

#### Full level (graph depth = 2)

```{code-cell} ipython3
dot_graph = output_dir / "prov_full.dot"
png_graph = output_dir / "prov_full.png"

# save provenance to dot file
# (generate pgn with dot -Tpng prov.dot -o prov.png)
save_prov_to_dot(
    prov_tracer,
    dot_graph,
    max_sub_prov_depth=2,
)

cmd = f"dot -Tpng {dot_graph} -o {png_graph}"
os.system(cmd)

from IPython.display import Image
Image(png_graph)
```
