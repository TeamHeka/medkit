__all__ = ["Pipeline", "PipelineStep"]

import dataclasses
from typing import Dict, List

from medkit.core.document import Document, Collection
from medkit.core.operation import ProcessingOperation


@dataclasses.dataclass
class PipelineStep:
    """`Pipeline` item describing how a processing operation is connected to other

    Attributes
    ----------
    operation:
        The operation to use at that step
    input_keys:
        For each input of `operation`, the key to use to retrieve the
        correspoding annotations (either retrieved from a document
        or generated by an earlier pipeline step)
    output_keys:
        For each output of `operation`, the key used to pass output annotations
        to the next Pipeline step. Can be empty if `operation` doesn't return
        new annotations.
    """

    operation: ProcessingOperation
    input_keys: List[str]
    output_keys: List[str]


class Pipeline:
    """Graph of processing operations to be applied to a document or a`collection
    of documents.

    A pipeline is made of pipeline steps, connecting together different processing
    operations by the use of input/output keys. Each operation can be seen as a node
    and the keys are its edge. Two operations can be chained by using the same string
    as an output key for the first operation and as an input key to the second.

    Steps must be added in the order of execution, there isn't any sort of depency
    detection mechanism.

    Existing annotations, that are not generated by an operation in the pipeline
    but rather that should be retrieved from documents, can be handled by associating
    an annotation label to an input key. Pipeline steps using this input key will then
    receive as input all the existing document annotations having the associated label.

    All annotations generated by each operation in the pipeline will be added to
    the corresponding document.
    """

    def __init__(self):
        self._steps: List[PipelineStep] = []
        self._labels_by_input_key: Dict[str, List[str]] = {}

    def add_step(self, step: PipelineStep):
        """Add a step to the pipeline

        Steps will be executed in the order in which they were added,
        so make sure to add first the steps generated data used by other steps.

        Params
        ------
        step:
            The step to add
        """
        self._steps.append(step)

    def add_label_for_input_key(self, label: str, key: str):
        """Associate an annotation label to an input key

        This is a way to feed into the pipeline annotations
        that are not the result of a pipeline step, but that
        are pre-attached to the document on which the pipeline
        is running.

        For all pipeline step using `key` as an input key,
        the annotations of the document having the label `label'
        will be used as input.

        It is possible to associate several labels to one key,
        as well as to associate a label to several keys

        Params
        ------
        label:
            The document annotation label
        key:
            The pipeline input key
        """
        assert label not in self._labels_by_input_key.get(
            key, []
        ), f"Label {label} is already associated to key {key}"

        if key not in self._labels_by_input_key:
            self._labels_by_input_key[key] = []
        self._labels_by_input_key[key].append(label)

    def run_on_doc(self, doc: Document):
        """Run the pipeline on a document.

        Params
        ------
        doc:
            The document on which to run the pipeline.
            Labels to input keys association will be used to retrieve existing
            annotations from this document, and all new annotations will also
            be added to this document.
        """
        # init dictionary that will hold all input/output annotations by key
        anns_by_key = {}

        # perform each step, get input annotations from anns_by_key
        # and/or document, and adding output annotations to anns_by_key
        for step in self._steps:
            self._perform_next_step(step, anns_by_key, doc)
            doc.add_operation(step.operation.description)

        # attach all generated annotations to document
        for output_anns in anns_by_key.values():
            for ann in output_anns:
                doc.add_annotation(ann)

    def run_on_collection(self, collection: Collection):
        """Run the pipeline on a collection of document.

        Params
        ------
        collection:
            The collection on which to run the pipeline.
            `run_on_doc()` will be called for each document
            in the collection.
        """
        for doc in collection.documents:
            self.run_on_document(doc)

    def _perform_next_step(self, step, anns_by_key, doc):
        # find input annotations for processing operation
        all_input_anns = []
        for input_key in step.input_keys:
            input_anns = self._get_input_anns_for_key(input_key, anns_by_key, doc)
            all_input_anns.append(input_anns)

        # call processing operation
        all_output_anns = step.operation.process(*all_input_anns)

        # wrap output in tuple if necessary
        # (processing operations performing in-place mutations
        # have no output and return None,
        # processing operations with single output may return a
        # single list instead of a tuple of lists)
        if all_output_anns is None:
            all_output_anns = tuple()
        elif not isinstance(all_output_anns, tuple):
            all_output_anns = (all_output_anns,)

        assert len(all_output_anns) == len(step.output_keys), (
            f"Number of outputs ({len(all_output_anns)}) does not match number of"
            f" output keys ({len(step.output_keys)})"
        )

        # store output anns
        for output_key, output_data in zip(step.output_keys, all_output_anns):
            if output_key not in anns_by_key:
                anns_by_key[output_key] = output_data
            else:
                anns_by_key[output_key] += output_data

    def _get_input_anns_for_key(self, key, anns_by_key, doc):
        if key not in anns_by_key and key not in self._labels_by_input_key:
            message = f"No annotations found for input key {key}"
            if any(key in s.input_keys for s in self._steps):
                message += (
                    " Did you add the steps in the correct order in the pipeline?"
                )
            raise RuntimeError(message)

        # retrieve input anns from outputs of previous steps
        input_anns = anns_by_key.get(key, [])

        # retrieve input anns from doc
        if key in self._labels_by_input_key:
            labels = self._labels_by_input_key[key]
            for label in labels:
                input_anns += doc.get_annotations_by_label(label)
        return input_anns