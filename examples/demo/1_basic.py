import os
from pathlib import Path
from pprint import pprint

import yaml

from medkit.core.text import TextDocument
from medkit.text.segmentation import SentenceTokenizer
from medkit.text.ner import RegexpMatcher
from medkit.text.context import NegationDetector

current_dir = Path(__file__).parent
input_dir = current_dir / "input"
output_dir = current_dir / "output_basic"

# load docs
docs = []
for filename in ["1.txt", "2.txt"]:
    with open(input_dir / filename) as f:
        docs.append(TextDocument(text=f.read()))


# init and configure operations
sentence_tokenizer = SentenceTokenizer()
negation_detector = NegationDetector(output_label="negation")
regexp_matcher_rules = RegexpMatcher.load_rules(
    current_dir / "regexp_matcher_rules.yml"
)
regexp_matcher = RegexpMatcher(rules=regexp_matcher_rules, attrs_to_copy=["negation"])

# annotate each doc
for doc in docs:
    anns = doc.get_annotations_by_label(TextDocument.RAW_TEXT_LABEL)
    anns = sentence_tokenizer.run(anns)
    negation_detector.run(anns)
    anns = regexp_matcher.run(anns)
    for ann in anns:
        doc.add_annotation(ann)

# print full doc data
doc = docs[0]
data = doc.to_dict()
pprint(data, sort_dicts=False)

# save it to yaml
os.makedirs(output_dir, exist_ok=True)
with open(output_dir / "doc.yml", mode="w") as f:
    yaml.dump(data, f, sort_keys=False)
