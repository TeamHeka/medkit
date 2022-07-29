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

# Loading and saving in Brat Format

+++

Brat is a web-based tool for text annotation. Brat uses the [standoff format](https://brat.nlplab.org/standoff.html).

Medkit supports the following types of brat annotations:
- Entities 
- Relations
- Attributes

Annotations with other types are ignored in the conversion process.

Consider this text file: 

+++

```
Le patient est prescrit du Lisinopril parce qu'il souffre d'hypertension.
Le patient avait une déficience en vitamines A et B.
```

+++

It could have the following brat annotation file:

```
T1	medication 27 37	Lisinopril
T2	disease 60 72	hypertension
T3	disease 95 105	déficience
A1	antecedent T3
T4	vitamin 109 117;119 120	vitamine A
T5	vitamin 109 117;124 126	vitamine B.
R1	treats Arg1:T1 Arg2:T2	
```

## Load brat into a Collection of TextDocuments

Medkit provides {class}`~medkit.text.brat.BratInputConverter` to load Brat Files.

```{tip}
You can set the provenance using:
```python
from medkit.core import ProvBuilder

# Define Input Converter and set provenance builder
prov_builder = ProvBuilder()
brat_converter = BratInputConverter()
brat_converter.set_prov_builder(prov_builder)
```

```{code-cell} ipython3
from pathlib import Path
from medkit.io.brat import BratInputConverter

# Define Input Converter 
brat_converter = BratInputConverter()

# Define path to brat
root_path = Path('.').resolve()
path_to_brat = root_path / "input"/"brat"

# Load brat into a collection of documents
collection = brat_converter.load(dir_path=path_to_brat)
medkit_doc = collection.documents[0]

# Explore annotations
print(f"The documents has {len(medkit_doc.get_annotations())} annotations")
entities_disease = medkit_doc.get_annotations_by_label("disease")
print(f"Where {len(entities_disease)} annotations have 'disease' as label")

```

```{code-cell} ipython3
# Show info in entities
for ent in entities_disease:
    print(ent.label, ent.spans,ent.text)
    if ent.attrs:
        print("\t -> Has an attribute:", ent.attrs[0].label)
```


## Save a collection to Brat

To save a Collection or list of `TextDocument` in Brat format, you can use {class}`~medkit.text.brat.BratOutputConverter`.

You can choose which medkit annotations and attributes to keep in the resulting Brat collection. 

Medkit generates an automatic `annotation.conf` so you can copy the collection directly to your brat data directory. 

```{code-cell} ipython3
from medkit.io.brat import BratOutputConverter

# Define Output Converter with default params,
# transfer all annotations and attributes
brat_output_converter = BratOutputConverter()

root_path = Path('.').resolve()
output_path = root_path / "_out"/"brat"

brat_output_converter.save(
  collection,  dir_path=output_path, doc_names=["doc_1"])
```
The collection is saved in the given path. By default the name is the document id, you can change it using the `doc_names` parameter. If the generated configuration does not include all values for each attribute, you can adjust the number of values when creating the converter.

:::{seealso}
cf. [Brat IO module](api:io:brat).
:::