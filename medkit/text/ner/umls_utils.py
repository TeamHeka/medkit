__all__ = ["UMLSEntry", "load_umls", "preprocess_term_to_match", "guess_umls_version"]

import dataclasses
from pathlib import Path
from typing import Iterator, List, Optional, Union
from tqdm import tqdm
import re

import unidecode


# based on https://github.com/GanjinZero/CODER/blob/master/coderpp/test/load_umls.py


@dataclasses.dataclass
class UMLSEntry:
    """Entry in MRCONSO.RRF file of a UMLS dictionary

    Attributes
    ----------
    cui:
        Unique identifier of the concept designated by the term
    ref_term:
        Original version of the term
    """

    cui: str
    term: str

    def to_dict(self):
        return dict(cui=self.cui, term=self.term)


def load_umls(
    mrconso_file: Union[str, Path],
    sources: Optional[List[str]] = None,
    languages: Optional[List[str]] = None,
    show_progress: bool = False,
) -> Iterator[UMLSEntry]:
    """Load all terms and associated CUIs found in a UMLS MRCONSO.RRF file

    Parameters
    ----------
    mrconso_file:
        Path to the UMLS MRCONSO.RRF file
    sources:
        Sources to consider (ex: ICD10, CCS) If none provided, CUIs and terms
        of all sources will be taken into account.
    languages:
        Languages to consider. If none provided, CUIs and terms of all languages
        will be taken into account
    show_progress:
        Whether to show a progressbar

    Returns
    -------
    Iterator[UMLSEntry]
        Iterator over all term entries found in UMLS install
    """
    mrconso_file = Path(mrconso_file)
    file_size = mrconso_file.stat().st_size
    luis_seen = set()

    with open(mrconso_file, encoding="utf-8") as fp:
        lines_iter = fp

        if show_progress:
            progress_bar = tqdm(
                total=file_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            )

        for line in lines_iter:
            if show_progress:
                line_size = len(line.encode("utf-8"))
                progress_bar.update(line_size)

            row = line.strip().split("|")
            cui = row[0]
            language = row[1]
            lui = row[3]
            source = row[11]
            term = row[14]

            if sources is not None and source not in sources:
                continue
            if languages is not None and language not in languages:
                continue
            if lui in luis_seen:
                continue

            luis_seen.add(lui)
            yield UMLSEntry(cui, term)

    if show_progress:
        progress_bar.close()


_BRACKET_PATTERN = re.compile("\\(.*?\\)")


def preprocess_term_to_match(
    term: str,
    lowercase: bool,
    normalize_unicode: bool,
    clean_nos: bool = True,
    clean_brackets: bool = True,
    clean_dashes: bool = True,
):
    """
    Preprocess a UMLS term for matching purposes

    Parameters
    ----------
    term: str
        Term to preprocess
    lowercase:
        Whether `term` should be lowercased
    normalize_unicode:
        Whether `term_to_match` should be ASCII-only (non-ASCII chars replaced by closest ASCII chars)
    clean_nos:
        Whether to remove "NOS"
    clean_brackets:
        Whether to remove brackets
    clean_dashes:
        Wehther to remove dashes
    """
    if lowercase:
        term = term.lower()
    if normalize_unicode:
        term = unidecode.unidecode(term)

    term = " " + term + " "
    if clean_nos:
        term = term.replace(" NOS ", " ").replace(" nos ", " ")
    if clean_brackets:
        term = _BRACKET_PATTERN.sub("", term)
    if clean_dashes:
        term = term.replace("-", " ")
    term = " ".join([w for w in term.split() if w])
    return term


def guess_umls_version(path: Union[str, Path]) -> str:
    """Try to infer UMLS version (ex: "2021AB") from any UMLS-related path

    Parameters
    ----------
    path:
        Path to the root directory of the UMLS install or any file inside that directory
    Returns
    -------
        UMLS version, estimated by finding the leaf-most folder in `path` that is not
        "META", "NET" nor "LEX", nor a subfolder of these folders
    """
    path = Path(path).resolve()
    if path.is_file():
        path = path.parent
    while any(dir_name in path.parts for dir_name in ("META", "NET", "LEX")):
        path = path.parent
    return path.name
