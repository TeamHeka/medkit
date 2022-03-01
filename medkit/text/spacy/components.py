from spacy import Language
from spacy.tokens import Doc


@Language.component(
    "medkit_merge_entities",
    requires=["doc.ents"],
    retokenizes=True,
)
def medkit_merge_entities(spacy_doc: Doc) -> Doc:
    """Merge entities into a single token.

    Parameters
    ----------
    spacy_doc:
        The Doc object from Spacy

    Returns
    -------
    Doc:
        The Doc object from Spacy with merged entities.
    """
    with spacy_doc.retokenize() as retokenizer:
        for ent in spacy_doc.ents:
            retokenizer.merge(ent)
    return spacy_doc
