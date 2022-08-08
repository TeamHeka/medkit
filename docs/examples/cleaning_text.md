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

# Cleaning text without destruction

+++

This example will show you how to use the class {class}`~medkit.text.preprocessing.eds_cleaner.EDSCleaner` class. A cleanup operation inspired by documents with formatting problems given previous conversion processes. 

## Loading a text to clean

Consider the following document:

```{code-cell} ipython3
from pathlib import Path
from medkit.core.text import TextDocument

file = Path("./input/text/text_to_clean.txt")
doc = TextDocument(text=file.read_text())
```
```{code-cell} ipython3
print(doc.text)
```
As we note, the text has:
- additional spaces;
- multiple newlines characters;
- long parentheses and numbers in English format.

This complicates text segmentation, it may be a good idea to clean up the text before segmenting or creating annotations.
  
## Using EDSCleaner to clean the document

When a `TextDocument` is created, medkit creates a `raw_segment` that stores the raw text of the document. That is the segment on which we run the cleanup operation.

In this case, we initialize the `EDS_cleaner` with `keep_endlines=True` to facilitate the visualization. Otherwise, the output segment would be a plain text with no newlines `(\n)` characters. 

```{code-cell} ipython3
from medkit.text.preprocessing import EDSCleaner

eds_cleaner = EDSCleaner(keep_endlines=True)
raw_segment = doc.raw_segment
clean_segment = eds_cleaner.run([raw_segment])[0]
print(clean_segment.text)

```

The class works on `Segments`. In the `run` method it performs various operations to delete or change characters of interest. By default it performs these operations:

* Changes points between uppercase letters by space
* Changes points between numbers to commas
* Clears multiple spaces and newline characters.

```{note}
There are two special operations that process parentheses and dots near French keywords such as Dr., Mme. and others. To enable/disable these operations you can use `handle_parentheses_eds` and `handle_points_eds`.
```
```{seealso}
For further information on the utilities used in this class, see {class}`~medkit.core.text.utils`

``` 
## Extract text from the clean text

Now that we have a clean text, we can run an operation on the new segment. We can detect the sentences, for example.


```{code-cell} ipython3
from medkit.text.segmentation import SentenceTokenizer

sentences = SentenceTokenizer().run([clean_segment])
for i,sent in enumerate(sentences):
  print(f"[{i}]:{sent.text!r}\n")
```

**A created sentence in detail**

The span of each generated sentence contains the modifications made by *eds_cleaner*. Let's look at the second sentence:  


```{code-cell} ipython3
sentence = sentences[1]
print(f"text={sentence.text!r}")
print("spans=\n","\n".join(f"{sp}" for sp in sentence.spans))
```

## Displaying in the original text

Since the sentence contains the information from the original span, it will always be possible to go back and display the information in the raw text. 

To get the original span, we can use {func}`~medkit.core.text.span_utils.normalize_spans`. Next, we can extract the raw text using {func}`~medkit.core.text.span_utils.extract`. 

```{code-cell} ipython3
from medkit.core.text.span_utils import normalize_spans, extract

spans_sentence = normalize_spans(sentence.spans)
extrated_text, spans = extract(raw_segment.text,raw_segment.spans,spans_sentence)
print(f"Sentence in the raw version:\n \"{extrated_text}\"")
```

Medkit combines these utilities to transform text and extract information without losing the raw text.  


