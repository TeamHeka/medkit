from pathlib import Path

import pytest

from medkit.core import ProvTracer
from medkit.core.text import Entity, Span
from medkit.text.ner.umls_coder_normalizer import UMLSCoderNormalizer


_PATH_TO_MR_CONSO_FILE = Path(__file__).parent / "sample_umls_data" / "MRCONSO.RRF"
_LANGUAGE = "ENG"
_MODEL = "GanjinZero/UMLSBert_ENG"
_ASTHMA_CUI = "C0004096"
_DIABETES_CUI = "C0011854"


@pytest.fixture(scope="module", autouse=True)
def _mocked_umls_embeddings_chunk_size(module_mocker):
    # force a very small precomputed embeddings chunk size so we can test behavior with
    # several chunks even though we have a very small sample MRCONSO.RRF
    # (cf test_nb_umls_embeddings_chunks())
    module_mocker.patch(
        "medkit.text.ner.umls_coder_normalizer._UMLS_EMBEDDINGS_CHUNK_SIZE", 2
    )


@pytest.fixture(scope="module")
def module_tmp_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("tmp_dir")


@pytest.fixture(scope="module")
def embeddings_cache_dir(module_tmp_dir):
    return module_tmp_dir / "umls_coder_cache"


@pytest.fixture(scope="module")
def normalizer(embeddings_cache_dir):
    return UMLSCoderNormalizer(
        umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
        language="ENG",
        model=_MODEL,
        embeddings_cache_dir=embeddings_cache_dir,
    )


def _get_entity(label, text):
    return Entity(label=label, spans=[Span(0, len(text))], text=text)


def test_basic(normalizer):
    """Basic behavior with 2 input entities"""

    entity_1 = _get_entity(label="disease", text="asthma")
    # intentional small typo in 2d entity
    entity_2 = _get_entity(label="disease", text="type 1 diabts")
    entities = [entity_1, entity_2]

    normalizer.run(entities)

    attrs = entity_1.get_attrs_by_label("umls")
    assert len(attrs) == 1
    attr_1 = attrs[0]
    assert attr_1.label == "umls"
    assert attr_1.value == _ASTHMA_CUI
    # exact match has 1.0 score
    assert attr_1.metadata["score"] == 1.0
    assert attr_1.metadata["normalized_term"] == "Asthma"
    assert attr_1.metadata["version"] == "sample_umls_data"

    attrs = entity_2.get_attrs_by_label("umls")
    assert len(attrs) == 1
    attr_2 = attrs[0]
    assert attr_2.label == "umls"
    assert attr_2.value == _DIABETES_CUI
    # approximate match has less than 1.0 score
    assert 0.7 <= attr_2.metadata["score"] < 1.0
    assert attr_2.metadata["normalized_term"] == "Type 1 Diabetes"


def _get_entities(nb_entities):
    entities = []
    for i in range(nb_entities):
        if i % 2:
            entity = _get_entity(label="disease", text="asthma")
        else:
            entity = _get_entity(label="disease", text="type 1 diabetes")
        entities.append(entity)
    return entities


def test_threshold(embeddings_cache_dir):
    """Threshold should leave some entities without normalization attributes when similarity is low
    """

    # 1st entity with small typo
    entity_1 = _get_entity(label="disease", text="type 1 diabets")
    # 2d entity with bigger typo
    entity_2 = _get_entity(label="disease", text="tpe 1 diabts")
    entities = [entity_1, entity_2]

    threshold = 0.9
    normalizer = UMLSCoderNormalizer(
        umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
        language=_LANGUAGE,
        model=_MODEL,
        embeddings_cache_dir=embeddings_cache_dir,
        threshold=threshold,
    )
    normalizer.run(entities)

    # 1st entity has normalization attribute because the score is bigger than threshold
    attr_1 = entity_1.get_attrs_by_label("umls")[0]
    assert attr_1.metadata["score"] >= threshold
    # 2d entity has no attribute because it is not similar enough
    assert len(entity_2.get_attrs_by_label("umls")) == 0


def test_max_nb_matches(embeddings_cache_dir):
    entity = _get_entity(label="disease", text="diabetes")

    max_nb_matches = 2
    normalizer = UMLSCoderNormalizer(
        umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
        language=_LANGUAGE,
        model=_MODEL,
        embeddings_cache_dir=embeddings_cache_dir,
        max_nb_matches=max_nb_matches,
    )
    normalizer.run([entity])

    assert len(entity.get_attrs_by_label("umls")) == max_nb_matches


@pytest.mark.parametrize(
    "input_size,batch_size",
    [(12, 1), (1, 12), (24, 12)],
)
def test_batch(embeddings_cache_dir, input_size, batch_size):
    """Behavior with various input length/batch size combinations"""

    entities = _get_entities(input_size)

    normalizer = UMLSCoderNormalizer(
        umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
        language=_LANGUAGE,
        model=_MODEL,
        embeddings_cache_dir=embeddings_cache_dir,
        batch_size=batch_size,
    )
    normalizer.run(entities)

    # check that result is identical to normalizing one by one
    entities_copy = _get_entities(input_size)
    for entity, entity_copy in zip(entities, entities_copy):
        attrs = entity.get_attrs_by_label("umls")
        assert len(attrs) == 1
        attr = attrs[0]
        normalizer.run([entity_copy])
        excepted_attr = entity_copy.get_attrs_by_label("umls")[0]
        assert attr.label == excepted_attr.label
        assert attr.value == excepted_attr.value


def test_nb_umls_embeddings_chunks(embeddings_cache_dir):
    """Enable chunk loading of precomputed umls embeddings
    Note that for tests, a chunk contains 2 embeddings
    (cf _mocked_umls_embeddings_chunk_size())
    """

    entity = _get_entity(label="disease", text="asthma")

    normalizer = UMLSCoderNormalizer(
        umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
        language=_LANGUAGE,
        model=_MODEL,
        embeddings_cache_dir=embeddings_cache_dir,
        nb_umls_embeddings_chunks=2,
    )
    normalizer.run([entity])

    # check that result is identical when using with direct loading of all precomputed umls embeddings
    entity_copy = _get_entity(label="disease", text="asthma")
    ref_normalizer = UMLSCoderNormalizer(
        umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
        language=_LANGUAGE,
        model=_MODEL,
        embeddings_cache_dir=embeddings_cache_dir,
    )
    ref_normalizer.run([entity_copy])

    attrs = entity.get_attrs_by_label("umls")
    assert len(attrs) == 1
    attr = attrs[0]
    expected_attr = entity_copy.get_attrs_by_label("umls")[0]
    assert attr.label == expected_attr.label
    assert attr.value == expected_attr.value


def test_inconsistent_params(module_tmp_dir):
    """Use UMLS embeddings dir containing embeddings pre-computed with different params
    """

    embeddings_cache_dir = module_tmp_dir / "umls_coder_cache_cls"
    # first, generate embeddings with "cls" method in umls_embeddings_dir
    _ = UMLSCoderNormalizer(
        umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
        language=_LANGUAGE,
        model=_MODEL,
        embeddings_cache_dir=embeddings_cache_dir,
        summary_method="cls",
    )

    # then try to reuse precomputed embedding but with MEAN method
    with pytest.raises(
        Exception,
        match=(
            r"Cache directory .* contains UMLS embeddings pre-computed with different"
            r" params"
        ),
    ):
        _ = UMLSCoderNormalizer(
            umls_mrconso_file=_PATH_TO_MR_CONSO_FILE,
            language=_LANGUAGE,
            model=_MODEL,
            embeddings_cache_dir=embeddings_cache_dir,
            summary_method="mean",
        )


def test_prov(normalizer):
    """Generated provenance"""

    entity_1 = _get_entity(label="disease", text="asthma")
    entity_2 = _get_entity(label="disease", text="type 1 diabetes")
    entities = [entity_1, entity_2]

    prov_tracer = ProvTracer()
    normalizer.set_prov_tracer(prov_tracer)
    entities = normalizer.run(entities)

    # data item uid and operation uid are correct
    attr_1 = entity_1.get_attrs_by_label("umls")[0]
    prov_1 = prov_tracer.get_prov(attr_1.uid)
    assert prov_1.data_item == attr_1
    assert prov_1.op_desc == normalizer.description

    # 1st attribute has 1st entity as source
    assert prov_1.source_data_items == [entity_1]
    # 2nd attribute has 2nd entity as source
    attr_2 = entity_2.get_attrs_by_label("umls")[0]
    prov_2 = prov_tracer.get_prov(attr_2.uid)
    assert prov_2.source_data_items == [entity_2]
