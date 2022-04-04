import os
from pathlib import Path
from pprint import pprint

import yaml

from medkit.core import DictStore, DocPipeline, Pipeline, PipelineStep, ProvBuilder
from medkit.core.text import TextDocument, TextAnnotation
from medkit.text.segmentation import SentenceTokenizer
from medkit.text.ner import RegexpMatcher
from medkit.text.context import NegationDetector
from medkit.tools import save_prov_to_dot

current_dir = Path(__file__).parent
input_dir = current_dir / "input"
output_dir = current_dir / "output_provenance_sub_graphs"

# init store and provenance builder
store = DictStore()
prov_builder = ProvBuilder(store)

# load docs
docs = []
for filename in ["1.txt", "2.txt"]:
    with open(input_dir / filename) as f:
        docs.append(TextDocument(text=f.read(), store=store))


# define context pipeline
class ContextPipeline(Pipeline):
    def __init__(i):
        sentence_tokenizer = SentenceTokenizer()
        negation_detector = NegationDetector(output_label="negation")
        steps = [
            PipelineStep(
                sentence_tokenizer, input_keys=["full_text"], output_keys=["sentences"]
            ),
            PipelineStep(negation_detector, input_keys=["sentences"], output_keys=[]),
        ]
        super().__init__(steps, input_keys=["full_text"], output_keys=["sentences"])


# init and configure operations
context_pipeline = ContextPipeline()
regexp_matcher_rules = RegexpMatcher.load_rules(
    current_dir / "regexp_matcher_rules.yml"
)
regexp_matcher = RegexpMatcher(rules=regexp_matcher_rules, attrs_to_copy=["negation"])

# build main pipeline using context pipeline
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

pipeline = DocPipeline(
    steps,
    labels_by_input_key={"full_text": [TextDocument.RAW_TEXT_LABEL]},
    output_keys=["entities"],
)

# set prov builder on pipeline
pipeline.set_prov_builder(prov_builder)
# run pipeline on docs
pipeline.run(docs)

# print full doc data
doc = docs[0]
data = doc.to_dict()
pprint(data, sort_dicts=False)

# save it to yaml
os.makedirs(output_dir, exist_ok=True)
with open(output_dir / "doc.yml", mode="w") as f:
    yaml.dump(data, f, sort_keys=False)


# save prov graph to dot file, with different level of details
# (generate pgn with dot -Tpng prov.dot -o prov.png)
prov_graph = prov_builder.graph


def data_item_formatter(d):
    return d.text if isinstance(d, TextAnnotation) else f"{d.label}:{d.value}"


def operation_formatter(o):
    return o.name


with open(output_dir / "prov.dot", mode="w") as file:
    save_prov_to_dot(
        prov_graph,
        store,
        file,
        data_item_formatter,
        operation_formatter,
        max_sub_graph_depth=0,
    )
with open(output_dir / "prov_intermediate.dot", mode="w") as file:
    save_prov_to_dot(
        prov_graph,
        store,
        file,
        data_item_formatter,
        operation_formatter,
        max_sub_graph_depth=1,
    )
with open(output_dir / "prov_full.dot", mode="w") as file:
    save_prov_to_dot(
        prov_graph,
        store,
        file,
        data_item_formatter,
        operation_formatter,
        max_sub_graph_depth=None,
    )
