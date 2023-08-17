# Tools

This page lists miscellaneous utility components.

:::{note}
For more details about public APIs, refer to
{mod}`medkit.tools`.
:::

## Save provenance to .dot

Helper function to generate [graphviz](https://graphviz.org/)-compatible .dot
files from provenance data. For more details, refer to
{func}`medkit.tools.save_prov_to_dot`.

## HuggingFace utils

Helper functions for operations using [HuggingFace](https://huggingface.co/) models. For more details,
refer to {mod}`medkit.tools.hf_utils`.

## mtsamples utils

:::{note}
For more details about mtsamples data, refer to {mod}`medkit.tools.mtsamples`
:::

The functions provided by this module automatically download mtsamples data into
a cache directory before loading / converting into medkit format.

For example, if you want to load the ten first mtsamples text documents:

```
from medkit.tools.mtsamples import convert_mtsamples_to_medkit, load_mtsamples

docs = load_mtsamples(nb_max=10)
```

## e3c corpus utils

:::{note}
For more details about e3c corpus data, refer to {mod}`medkit.tools.e3c_corpus`
:::

The E3C corpus is available for download on:
* the [E3C Project Web Site](https://live.european-language-grid.eu/catalogue/corpus/7618/download/)
* or the [Github Project - V2.0.0](https://github.com/hltfbk/E3C-Corpus/tree/v2.0.0)

Once downloaded and unzipped, you may :

* load the data collection into medkit text documents

```
from pathlib import Path
from medkit.tools.e3c_corpus import load_data_collection

data_collection_layer1 = Path("/tmp/E3C-Corpus-2.0.0/data_collection/French/layer1")

docs = load_data_collection(data_collection_layer1)
```

* convert the data collection to medkit text documents.

```
from pathlib import Path
from medkit.tools.e3c_corpus import convert_data_collection_to_medkit

data_collection = Path("/tmp/E3C-Corpus-2.0.0/data_collection/French")
layers = ["layer1", "layer2", "layer3"]

for layer in layers:
    dir_path = data_collection / layer
    medkit_file = f"medkit_e3c_{layer}.jsonl"
    convert_data_collection_to_medkit(
        dir_path=dir_path, output_file=medkit_file
    )
```

* load the annotated data into medkit text documents

```
from pathlib import Path
from medkit.tools.e3c_corpus import load_data_annotation

data_annotation_layer1 = Path("/tmp/E3C-Corpus-2.0.0/data_annotation/French/layer1")

docs = load_data_annotation(data_annotation_layer1)
```

* convert the annotated data to medkit text documents.

```
from pathlib import Path
from medkit.tools.e3c_corpus import convert_data_annotation_to_medkit

data_annotation = Path("/tmp/E3C-Corpus-2.0.0/data_annotation/French")
layers = ["layer1", "layer2"]

for layer in layers:
    dir_path = data_annotation / layer
    medkit_file = f"medkit_e3c_annotated_{layer}.jsonl"
    convert_data_annotation_to_medkit(
        dir_path=dir_path, output_file=medkit_file
    )
```
