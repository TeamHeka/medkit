---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.0
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Loading and converting from Spacy

+++

[spaCy](https://spacy.io/) is a library for advanced Natural Language Processing in Python. Medkit can load spacy documents with entities, attributes (custom extensions) and groups of spans. The module is configurable according to use cases. 

```{note}
For this example, you should download the french spacy model. You can download it using:
```

```{code-cell} ipython3
:tags: [remove-output]

!python -m spacy download fr_core_news_sm
```

Consider the following spacy document:

```{code-cell} ipython3
import spacy

# Load French tokenizer, tagger, parser and NER
nlp = spacy.load("fr_core_news_sm")

# Process a document 
text = """Anna Euler habite à Brest. La patient a été transférée."""
spacy_doc = nlp(text)

# Add noun_chunk as a span group
spacy_doc.spans["NOUN_CHUNKS"] = list(spacy_doc.noun_chunks)

# Find named entities
print("Entities: ")
for entity in spacy_doc.ents:
    print(entity.text, entity.label_)
    
print("Span groups:\n", spacy_doc.spans)

```

## Load spacy docs into a Collection of TextDocuments

The class {class}`~medkit.text.spacy.SpacyInputConverter` is in charge of converting spacy Docs into a collection of TextDocuments. By default, since its parameters are set to `None`, it loads all entities, span groups and extension 
attributes for each `SpacyDoc` object.

You can choose the list of entities, spans or attributes of interest when configuring the input converter.

```{tip}
You can set the provenance using:
```python
from medkit.core import ProvBuilder

# Define Input Converter and set provenance builder
prov_builder = ProvBuilder()
spacy_input_converter = SpacyInputConverter()
spacy_input_converter.set_prov_builder(prov_builder)
```

```{code-cell} ipython3
from medkit.io.spacy import SpacyInputConverter

# Define Input Converter 
spacy_input_converter = SpacyInputConverter()

# Load spacy doc into a collection of documents
collection = spacy_input_converter.load([spacy_doc])
medkit_doc = collection.documents[0]

# Explore annotations
print(f"The medkit doc has {len(medkit_doc.get_annotations())} annotations.")

```

```{code-cell} ipython3


# Show info in entities
print("\nEntities loaded from spacy in medkit: ")
for ent in medkit_doc.get_entities():
    print(ent.label, ent.spans,ent.text)

# Show span groups
noun_chunks = medkit_doc.get_annotations_by_label("NOUN_CHUNKS")

print("\nSpan group loaded from spacy in medkit:")
for noun in noun_chunks:
    print(noun.label, noun.spans,noun.text)
  
```

## Convert a collection of TextDocument to SpacyDocs

Similarly it is possible to convert a list/Collection of TextDocument to Spacy using {class}`~medkit.text.spacy.SpacyOutputConverter`. You will need to provide an `nlp` object that tokenizes and generates the document with the raw text as reference.

You can choose which medkit annotations and attributes to convert. Likewise, you can apply the nlp object to the converted documents with the `apply_nlp_spacy` parameter. 


```{code-cell} ipython3
from medkit.io.spacy import SpacyOutputConverter

# define Output Converter with default params
spacy_output_converter = SpacyOutputConverter(nlp=nlp)

# Convert a list of TextDocument 
new_spacy_docs = spacy_output_converter.convert([medkit_doc])
new_spacy_doc = new_spacy_docs[0]

# Explore new spacy doc
print("Text of spacy doc from TextDocument:\n",new_spacy_doc.text)
```

```{code-cell} ipython3
print("Entities: ")
for entity in new_spacy_doc.ents:
    print(entity.text, entity.label_)
    
print("Span groups:", new_spacy_doc.spans)
```
:::{seealso}
cf. [Spacy IO module](api:io:spacy).
:::
