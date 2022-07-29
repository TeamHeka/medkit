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

In the medical domain, it is common to find documents that are difficult to process. A text may include special characters, unwanted newline characters '\n' or multiple spaces. 

Consider a document with the following format:

```{code-cell} ipython3
text = """Depuis la mise en place du traitement, 

le papa note clairement une nette

amélioration du 

comportement."""
```

## Removing the character `\n` using text utils

Medkit has some functions already implemented to clean up text in special cases such as ending lines, multiple spaces or text near keywords.  Here we use  {func}`~medkit.core.text.utils.clean_newline_character`.


```{code-cell} ipython3
from medkit.core.text import TextDocument
from medkit.core.text.utils import clean_newline_character

def print_info(title,text,spans): 
    # show info about text and spans
    info = f"--- {title} ---\n\n"
    info += f"\"{text}\"\n"
    info += f"\n--- Spans ---\n"
    info += "\n".join(f"- {span}" for span in spans)
    print(info)

doc = TextDocument(text=text)
raw_segment = doc.raw_segment
print_info("Original raw text",raw_segment.text,raw_segment.spans)
```
**Using clean_newline_character**
```{code-cell} ipython3
new_text, new_spans = clean_newline_character(raw_segment.text,raw_segment.spans)
print_info("Clean text",new_text,new_spans)
```

## Extract text from the clean text

+++

You can now create a new segment with the clean version and find terms. 

Imagine `nette amélioration` is a term of interest. In the clean text this match starts in the character **68** and ends in the character **86**. 

To extract the information you can use {func}`~medkit.core.text.span_utils.extract`.

```{code-cell} ipython3
from medkit.core.text import Segment
from medkit.core.text.span_utils import extract, normalize_spans

# Create a new segment 
clean_segment = Segment(
  label="CLEAN_TEXT", text = new_text, spans = new_spans
)

# Extract term from the new segment
term_text, term_spans = extract(
  clean_segment.text,clean_segment.spans,[(68,86)]
)
print_info("Term found in the clean text",term_text,term_spans)
```

You can see that `term_spans` saves the modifications.

Now, to get the same term in the original annotation, you can use the following:

* {func}`~medkit.core.text.span_utils.normalize_spans` to get the original span.
* `extract` to get the term in its original version.

```{code-cell} ipython3
# Normalize spans of the term
span_original = normalize_spans(term_spans)[0]

# Get the term in the raw segment
raw_term_text, raw_term_spans = extract(
    raw_segment.text,raw_segment.spans,[(span_original.start,span_original.end)]
)

print_info("Term found in the raw text",raw_term_text,raw_term_spans)
```

