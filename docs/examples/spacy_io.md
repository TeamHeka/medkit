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
from spacy.tokens import Span as SpacySpan

# Load French tokenizer, tagger, parser and NER
nlp = spacy.load("fr_core_news_sm")

# Create a spacy document 
text = """Parcours patient:
Anna Euler habite à Brest. Elle a été transférée."""
spacy_doc = nlp(text)

#  Spacy adds entities, here we add a span 'SECTION' as an example
spacy_doc.spans["SECTION"] = [SpacySpan(spacy_doc, 0, 2, "header")]
```

**Description of the spacy document**

---
* Entities
---

```{code-cell} ipython3
from spacy import displacy

displacy.render(spacy_doc, style="ent")
```

---
* Spans
---

```{code-cell} ipython3
displacy.render(spacy_doc, style="span",options={"spans_key": "SECTION"})

```

The spacy document has **2** entities and **1** span groups called `SECTION`.

Let's see how to convert this spacy doc in a `TextDocument` with annotations.

## Load spacy docs into a Collection of TextDocuments

The class {class}`~medkit.io.spacy.SpacyInputConverter` is in charge of converting spacy Docs into a collection of TextDocuments. By default, it loads all entities, span groups and extension  attributes for each SpacyDoc object, but you can use the `entities`, `span_groups` and `attrs` parameters to specify which items should be converted, based on their labels.

```{tip}
You can enable the provenance tracing using the method `set_prov_builder` with a {class}`~medkit.core.ProvBuilder` object.

```


```{code-cell} ipython3
from medkit.io.spacy import SpacyInputConverter

# Define Input Converter 
spacy_input_converter = SpacyInputConverter()

# Load spacy doc into a collection of documents
collection = spacy_input_converter.load([spacy_doc])
medkit_doc = collection.documents[0]
```

**Description of the resulting Text document**
+++

```{code-cell} ipython3
print(f"The medkit doc has {len(medkit_doc.get_annotations())} annotations.")
print(f"The medkit doc has {len(medkit_doc.get_entities())} entities.")
print(f"The medkit doc has {len(medkit_doc.get_annotations_by_label('SECTION'))} spans.")
```

**Visualizing Medkit annotations**

As explained in other tutorials, we can view medkit annotations using `displacy`. 

---
* Entities loaded from spacy in medkit
---

```{code-cell} ipython3
from medkit.text.spacy.displacy_utils import medkit_doc_to_displacy

# getting entities in displacy format
entities_data = medkit_doc_to_displacy(medkit_doc)
displacy.render(entities_data, style="ent",manual=True)
```

---
* Spans loaded from spacy in medkit
---

```{code-cell} ipython3

# getting spans from 'SECTION' in displacy format
# In this case, we display the original label from spacy 
section_data = medkit_doc_to_displacy(medkit_doc,["SECTION"],lambda sp: sp.metadata["name"])
displacy.render(section_data, style="ent",manual=True)
```

## Convert a collection of TextDocument to SpacyDocs

Similarly it is possible to convert a list/Collection of TextDocument to Spacy using {class}`~medkit.io.spacy.SpacyOutputConverter`. You will need to provide an `nlp` object that tokenizes and generates the document with the raw text as reference. By default, it converts all medkit annotations and attributes to Spacy, but you can use  `anns_labels` and `attrs` parameters to specify which items should be converted. 

```{code-cell} ipython3
from medkit.io.spacy import SpacyOutputConverter

# define Output Converter with default params
spacy_output_converter = SpacyOutputConverter(nlp=nlp)

# Convert a list of TextDocument 

spacy_docs_medkit = spacy_output_converter.convert([medkit_doc])
spacy_doc_medkit = spacy_docs_medkit[0]

# Explore new spacy doc
print("Text of spacy doc from TextDocument:\n",spacy_doc_medkit.text)
```

**Description of the resulting Spacy document**

---
* Entities exported to spacy
---

```{code-cell} ipython3
displacy.render(spacy_doc_medkit, style="ent")
```

---
* Spans exported to spacy
---

```{code-cell} ipython3
displacy.render(spacy_doc_medkit, style="span",options={"spans_key": "SECTION"})

```
:::{seealso}
cf. [Spacy IO module](api:io:spacy).
:::
