from __future__ import annotations

__all__ = ["SyntagmaTokenizer"]

import dataclasses
import pathlib
import re
from typing import Iterator, List, Optional, Tuple

import yaml

from medkit.core.text import Segment, SegmentationOperation, span_utils

_DEFAULT_SYNTAGMA_DEFINITION_RULES = (
    pathlib.Path(__file__).parent / "default_syntagma_definition.yml"
)


@dataclasses.dataclass
class DefaultConfig:
    output_label = "SYNTAGMA"
    keep_separator = True


class SyntagmaTokenizer(SegmentationOperation):
    """Syntagma segmentation annotator based on provided separators"""

    def __init__(
        self,
        separators: Tuple[str, ...],
        output_label: str = DefaultConfig.output_label,
        keep_separator: bool = DefaultConfig.keep_separator,
        uid: Optional[str] = None,
    ):
        """
        Instantiate the syntagma tokenizer

        Parameters
        ----------
        separators: Tuple[str, ...]
            The tuple of regular expressions corresponding to separators.
        output_label: str, Optional
            The output label of the created annotations.
            Default: "SYNTAGMA" (cf. DefaultConfig)
        keep_separator: bool, Optional
            If True, the separators are kept in the detected syntagma
            If False, the syntagma text does not include the separator
            Default: True (cf. DefaultConfig)
        uid: str, Optional
            Identifier of the tokenizer
        """
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        self.output_label = output_label
        self.separators = separators
        self.keep_separator = keep_separator

    def run(self, segments: List[Segment]) -> List[Segment]:
        """
        Return syntagmes detected in `segments`.

        Parameters
        ----------
        segments:
            List of segments into which to look for sentences

        Returns
        -------
        List[Segments]:
            Syntagmas segments found in `segments`
        """
        return [
            syntagma
            for segment in segments
            for syntagma in self._find_syntagmas_in_segment(segment)
        ]

    def _find_syntagmas_in_segment(self, segment: Segment) -> Iterator[Segment]:
        regex_rule = (
            "(?P<blanks> *)"  # Blanks at the beginning of the syntagmas
            + "(?P<syntagma>.+?)"  # Syntagma to detect
            + "(?P<separator>"  # Separator
            + "|".join(self.separators)
            + "|$)"  # including the last syntagma without end separator
        )
        pattern = re.compile(regex_rule, flags=re.DOTALL)

        sep_exists = False
        start = 0

        for match in pattern.finditer(segment.text):
            # Ignore empty syntagmas
            if len(match.group("syntagma").strip()) == 0:
                continue

            start = match.start("syntagma") if not sep_exists else start
            end = match.end("syntagma")

            # Extract raw span list from regex match ranges
            text, spans = span_utils.extract(
                text=segment.text,
                spans=segment.spans,
                ranges=[(start, end)],
            )

            # Give next syntagma start if we want to keep separator
            sep_exists = self.keep_separator
            if sep_exists:
                start = match.start("separator")

            syntagma = Segment(
                label=self.output_label,
                spans=spans,
                text=text,
            )

            if self._prov_tracer is not None:
                self._prov_tracer.add_prov(
                    syntagma, self.description, source_data_items=[segment]
                )

            yield syntagma

    @classmethod
    def get_example(cls, keep_separator=True):
        config_path = _DEFAULT_SYNTAGMA_DEFINITION_RULES
        separators = cls.load_syntagma_definition(config_path, encoding="utf-8")
        syntagma_tokenizer = cls(separators=separators, keep_separator=keep_separator)
        return syntagma_tokenizer

    @staticmethod
    def load_syntagma_definition(
        filepath: pathlib.Path, encoding: Optional[str] = None
    ) -> Tuple[str, ...]:
        """
        Load the syntagma definition stored in yml file

        Parameters
        ----------
        filepath:
            Path to a yml file containing the syntagma separators
        encoding
            Encoding of the file to open

        Returns
        -------
        Tuple[str, ...]:
            Tuple containing the separators
        """

        with open(filepath, mode="r", encoding=encoding) as f:
            config = yaml.safe_load(f)

        syntagma_seps = tuple(str(sep) for sep in config["syntagmas"]["separators"])

        return syntagma_seps
