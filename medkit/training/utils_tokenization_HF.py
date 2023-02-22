from typing import Dict, List
from medkit.core.text import Entity, Segment

from transformers.tokenization_utils_fast import EncodingFast


def get_labels_aligned_from_tokens(
    text_tokenized: EncodingFast,
    segment: Segment,
    entities: List[Entity],
    use_bilou_scheme=True,
) -> List[str]:
    offset_segment = segment.spans[0].start
    labels = ["O"] * len(text_tokenized)

    for ent in entities:
        label = ent.label
        start_char = ent.spans[0].start - offset_segment
        end_char = ent.spans[-1].end - offset_segment
        tokens_entity = set()

        for idx in range(start_char, end_char):
            token_id = text_tokenized.char_to_token(idx)
            if token_id is not None:
                tokens_entity.add(token_id)

        tokens_entity = sorted(list(tokens_entity))

        if not tokens_entity:
            continue

        if len(tokens_entity) == 1:
            prefix = "U" if use_bilou_scheme else "B"
            labels[tokens_entity[0]] = f"{prefix}-{label}"
        else:
            labels[tokens_entity[0]] = f"B-{label}"
            prefix = "L" if use_bilou_scheme else "I"
            labels[tokens_entity[-1]] = f"{prefix}-{label}"

            inside_tokens = tokens_entity[1:-1]
            for token_idx in inside_tokens:
                labels[token_idx] = f"I-{label}"
    return labels


def get_labels_ids_from_anns(
    text_encoding: EncodingFast,
    segment: Segment,
    entities: List[Entity],
    label_to_id: Dict[str, int],
    use_bilou_scheme: bool = True,
    tag_all_labels: bool = True,
):
    special_tokens_mask = text_encoding.special_tokens_mask
    labels = get_labels_aligned_from_tokens(
        text_encoding, segment, entities, use_bilou_scheme=use_bilou_scheme
    )

    labels_ids = [-1] * len(labels)
    words = text_encoding.word_ids

    prev_word = None
    for idx, label in enumerate(labels):
        if special_tokens_mask[idx]:
            continue

        current_word = words[idx]
        if current_word != prev_word:
            # tag the first token of the word
            labels_ids[idx] = label_to_id[label]
            prev_word = current_word

        if tag_all_labels:
            labels_ids[idx] = label_to_id[label]
    return labels_ids
