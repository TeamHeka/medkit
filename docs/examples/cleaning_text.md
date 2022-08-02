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

This tutorial will show you how to use the class {class}`~medkit.text.preprocessing.eds_cleaner.EDSCleaner` class. A cleanup operation inspired by documents with formatting problems given previous conversion processes. 


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
As we can see, the text has:
- additional spaces;
- multiple newlines characters;
- long parentheses and numbers in English format.
  
## Using EDSCleaner 

The class works on `Segment` objects. In the `run` method it performs various operations to delete or change characters of interest. By default it performs these operations:

* Changes points between uppercase letters by space
* Changes points between numbers to commas
* Clears multiple spaces and newline characters.

```{note}
There are two special operations that process parentheses and dots near French keywords such as Dr., Mme. and others. To enable/disable these operations you can use `handle_parentheses_eds` and `handle_points_eds`.
```
```{seealso}
For further information on the utilities used in this class, see {class}`~medkit.core.text.utils`

``` 

Let's clean the segment keeping the endlines characters. 

```{code-cell} ipython3
from medkit.text.preprocessing import EDSCleaner

eds_cleaner = EDSCleaner(keep_endlines=True)
clean_segment = eds_cleaner.run([doc.raw_segment])[0]
print(clean_segment.text)

```
## Extract text from the clean text

Since the clean segment contains the information from the original span, it will always be possible to go back and display the information in the raw text. Let's imagine we want to section into sentences. 

```{code-cell} ipython3
from medkit.text.segmentation import SentenceTokenizer

```
