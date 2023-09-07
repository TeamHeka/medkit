# Fine-tuning a Transformers model with medkit

```{note}
This example may require optional modules from medkit, use the following to install them:

`pip install medkit-lib[training,hf-entity-matcher]`
```
In recent years, Large Language Models (LLMs) have achieved very good performance in natural language processing (NLP) tasks.  However, training a LLM (involving billions of parameters) from scratch requires a lot of resources and large quantities of text. 

Since these models are trained on general domain data, they learn complex patterns. We can adapt (fine-tune) the last layers to a specific task using our data and low resources. LLMs are PreTrained and accessible with libraries like [🤗 **Transformers**](https://huggingface.co/docs/transformers/index). Medkit has some components to fine-tune these models.

## Prepare DrBert for entity recognition 

In this example, we show how to fine-tune **DrBERT: A PreTrained model in French for Biomedical and Clinical domains** to detect the following entities: `problem`, `treatment`, `test` using the **medkit Trainer**. 

[DrBert](https://huggingface.co/Dr-BERT/DrBERT-4GB-CP-PubMedBERT)[^footnote1] is a French RoBERTa trained in open source corpus of french medical documents for masked language modeling. As mentioned before, we can change the specific task, for example, to classify entities. 

[^footnote1]:Yanis Labrak, Adrien Bazoge, Richard Dufour, Mickael Rouvier, Emmanuel Morin, Béatrice Daille, and Pierre-Antoine Gourraud. (2023). DrBERT: A Robust Pre-trained Model in French for Biomedical and Clinical domains.

### Using a custom medkit dataset

Let's start by defining a dataset using medkit documents. For this example, we use `CorpusCASM2`, an internal corpus with clinical cases annotated by master students. The corpus contains more than 5000 medkit documents (~ phrases) with entities to detect. The splits are predefined so, all we need to do is use the path of the desired split (`train` or `validation`) to load the documents.

:::{tip}
You can test this tutorial with your data. You can create medkit documents, add entities and export them to **JSONL** files.

```python
from medkit.core.text import TextDocument, Entity, Span
from medkit.io.medkit_json import save_text_documents

document = TextDocument(
    "Your custom phrase with entities",
    anns=[Entity(label="CUSTOM", spans=[Span(24, 32)], text="entities")],
)
# save your list of documents
train_docs = [document]
save_text_documents(train_docs, output_file="./train.jsonl")
```
You may refer to {mod}`~.io.medkit_json` for more information.
:::

```python
from torch.utils.data import Dataset
from medkit.io.medkit_json import load_text_documents

class CorpusCASM2(Dataset):
    """A dataset of clinical cases from the CORPUS CAS(medkit--version)"""

    def __init__(self, split):
        print(f"Creating CorpusCASM2 corpus {split}")
        self.labels_set = ["treatment", "problem", "test"]
        data_path = f"{split}.jsonl"
        self.documents = [doc for doc in load_text_documents(data_path)]

    def __getitem__(self, idx):
        return self.documents[idx]

    def __len__(self):
        return len(self.documents)
```

Just to see how a document looks, let's print the first example from the test dataset.

```python
doc = CorpusCASM2(split="test")[0]
msg = "|".join(f"'{entity.label}':{entity.text}" for entity in doc.anns.entities)
print(f"Text: '{doc.text}'\n{msg}")
```

```
Text: 'Une tachycardie et une fibrillation ventriculaire ont été observées.'
'problem':tachycardie |'problem': fibrillation ventriculaire
```

We can now define the datasets to use with the trainer.

```python
train_dataset = CorpusCASM2(split="train")
val_dataset = CorpusCASM2(split="validation")
```

### Creating an entity matcher trainable

Once documents have been collected, we need a component that implements the {class}`~.training.TrainableComponent` protocol.

Medkit supports **Entity detection** with HuggingFace models in inference and fine-tune context. The {class}`~.text.ner.hf_entity_matcher.HFEntityMatcher` expose its trainable version as a ready-to-use component. It defines the preprocessing, forward and its optimizer. 

```{seealso}
More info about this component in {class}`~.text.ner.hf_entity_matcher_trainable.HFEntityMatcherTrainable`
```

Let's define a trainable instance for this example. 

```python
from medkit.text.ner.hf_entity_matcher import HFEntityMatcher

hf_config = dict(
    model_name_or_path="Dr-BERT/DrBERT-4GB-CP-PubMedBERT",  # name in HF hub
    labels=["problem", "treatment", "test"],  # labels to fine-tune
    tokenizer_max_length=128,  # max length per item
    tagging_scheme="iob2",  # scheme to tag documents
    tag_subtokens=False,  # only tag the first token by word
)
hf_trainable = HFEntityMatcher.make_trainable(**hf_config)
```

## Fine-tuning with medkit Trainer 

At this point, we have prepared the data and the component to fine-tune. All we need to do is define the trainer with its configuration.

```python
from medkit.training import Trainer,TrainerConfig

trainer_config = TrainerConfig(
    output_dir="DrBert-CASM2",  # output directory
    batch_size=4,
    do_metrics_in_training=False,
    learning_rate=5e-6,
    nb_training_epochs=5,
    seed=0,
)

trainer = Trainer(
    component=hf_trainable,  # trainable component
    config=trainer_config,  # configuration
    train_data=train_dataset,  # training documents
    eval_data=val_dataset,  # eval documents
)

history = trainer.train()
```

### Training history

The trainer has a callback to display basic training information like `loss`, `time` and `metrics` if required, the method `trainer.train()` returns a dictionary with the training history and saves a checkpoint with the tuned model.

An example of log:
```
2023-05-03 21:13:07,304 - DefaultPrinterCallback - INFO - Training metrics : loss:   0.219
2023-05-03 21:13:07,305 - DefaultPrinterCallback - INFO - Evaluation metrics : loss:   0.20|
2023-05-03 21:13:07,306 - DefaultPrinterCallback - INFO - Epoch state: |epoch_id:   5 | time: 2348.17s
2023-05-03 21:13:07,307 - DefaultPrinterCallback - INFO - Saving checkpoint in DrBert-CASM2/checkpoint_03-05-2023_21:13
```
____

### Adding metrics in training

By default, only the loss configured by the trainable component is computed during the training / evaluation loop. We can add more metrics using a class that implements {class}`~.training.utils.MetricsComputer`. For entity detection, we can instantiate {class}`~.text.metrics.ner.SeqEvalMetricsComputer` directly. This object process and compute the metrics during training (using PyTorch Tensors). 

```python
from medkit.text.metrics.ner import SeqEvalMetricsComputer

mc_seqeval = SeqEvalMetricsComputer(
    id_to_label=hf_trainable.id_to_label, # mapping int value to tag
    tagging_scheme=hf_trainable.tagging_scheme, # tagging scheme to compute
    return_metrics_by_label= True, # include metrics by label in results
)
```

```{warning}
The **Trainer** updates the trainable component (~ model's weights) during training, if you want to run a new experiment, you need to create a new instance of the **trainable component**.
```

**Running with metrics**

:::{note}
By default, the Trainer only computes custom metrics using eval data. You can set `do_metrics_in_training=True` in the trainer configuration to also compute custom metrics using training data.
:::

```python
trainer_with_metrics = Trainer(
    component=HFEntityMatcher.make_trainable(**hf_config),  # a new instance 
    config=trainer_config,  # configuration
    train_data=train_dataset,  # training documents
    eval_data=val_dataset,  # eval documents    
    metrics_computer=mc_seqeval 
)

history_with_metrics = trainer.train()
```

Custom metrics are in `history_with_metrics` and the logs looks like this:

```
2023-05-04 20:33:59,128 - DefaultPrinterCallback - INFO - Training metrics : loss:   0.227
2023-05-04 20:33:59,129 - DefaultPrinterCallback - INFO - Evaluation metrics : loss:   0.286|overall_precision:   0.626|overall_recall:   0.722|overall_f1-score:   0.670|overall_support:3542.000|overall_acc:   0.899|problem_precision:   0.609|problem_recall:   0.690|problem_f1-score:   0.647|problem_support:1812.000|test_precision:   0.667|test_recall:   0.780|test_f1-score:   0.719|test_support: 937.000|treatment_precision:   0.614|treatment_recall:   0.728|treatment_f1-score:   0.666|treatment_support: 793.000
```
## Detecting entities in inference

Now we have a entity matcher fine-tuned with our custom dataset. We can use the last checkpoint to define a {class}`~.text.ner.hf_entity_matcher.HFEntityMatcher` and detect `problem`, `treatment`, `test` entities in french documents.

:::{hint}
In this version, the trainer saves **one** checkpoint at the end of training. The path will be `{trainer_config.output_path}/checkpoint_{DATETIME_END_TRAINING}`
:::


```python
from medkit.core.text import TextDocument
from medkit.text.ner.hf_entity_matcher import HFEntityMatcher

matcher = HFEntityMatcher(model="./DrBert-CASM2/checkpoint_03-05-2023_21:13")

test_doc = TextDocument("Elle souffre d'asthme mais n'a pas besoin d'Allegra")

# detect entities in the raw segment
detected_entities = matcher.run([test_doc.raw_segment]) 
msg = "|".join(f"'{entity.label}':{entity.text}" for entity in detected_entities)
print(f"Text: '{test_doc.text}'\n{msg}")
```

```
Text: "Elle souffre d'asthme mais n'a pas besoin d'Allegra"
'problem':asthme|'treatment':Allegra
```
**References**

