import re
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union, ValuesView, Dict
import json
from smart_open import open

from medkit.core import (
    Attribute,
    InputConverter,
    OutputConverter,
    ProvTracer,
    generate_id,
    OperationDescription,
)
from medkit.core.text import (
    TextAnnotation,
    Entity,
    Relation,
    Segment,
    Span,
    TextDocument,
    span_utils,
)


JSONL_EXT =".jsonl"
TEXT_EXT = ".txt"


logger = logging.getLogger(__name__)


class DoccannoJsonlConverter(InputConverter):
    """Class in charge of converting doccano annotations from jsonl"""

    def __init__(self, uid: Optional[str] = None):
        if uid is None:
            uid = generate_id()

        self.uid = uid
        self._prov_tracer: Optional[ProvTracer] = None

    @property
    def description(self) -> OperationDescription:
        return OperationDescription(
            uid=self.uid,
            name=self.__class__.__name__,
            class_name=self.__class__.__name__,
        )

    def set_prov_tracer(self, prov_tracer: ProvTracer):
        self._prov_tracer = prov_tracer

    def load(
        self,
        file_path: Union[str, Path],
        jsonl_ext: str = JSONL_EXT,

    ) -> List[TextDocument]:
        """
        Create a list of TextDocuments from a folder containing jsonl files from docanno.

        Parameters
        ----------
        dir_path:
            The path to the directory containing the  jsonl files 


        Returns
        -------
        List[TextDocument]
            The list of TextDocuments
        """
        documents = list()
        file_path = Path(file_path)

        
        

        ann_path = file_path.with_suffix(jsonl_ext)

            
        documents = self.load_doc(ann_path=ann_path)
            


        if not documents:
            logger.warning(f"Didn't load any document from path {file_path}")

        return documents

    def load_doc(
        self, ann_path: Union[str, Path], 
    ) -> TextDocument:
        """
        Create a TextDocument from a .jsonl file 

        Parameters
        ----------

        ann_path:
            The path to the jsonl docanno annotation file.

        Returns
        -------
        TextDocument
            The document containing the text and the annotations
        """

        ann_path = Path(ann_path)



        text_anns = self.load_annotations(ann_path)
        
        documents = list()
        for dict_i in text_anns :
            
            doc = TextDocument(text=dict_i["text"], metadata=dict_i["id"])

            for ann in dict_i["anns"]:
                doc.anns.add(ann)
            
        documents.append(doc)
        return documents

    def load_annotations(self, ann_file: Union[str, Path]) -> List[TextAnnotation]:
        """
        Load a .jsonl file and return the rax text and a list of
        :class:`~medkit.core.text.annotation.Annotation` objects.

        Parameters
        ----------
        ann_file:
            Path to the .jsonl file.
        """

       


        
        

        with open(ann_file, 'r') as json_file:
            doccano_doc = list(json_file)
        text_anns = list()
        

        for doc_i in doccano_doc:
            doc_ann=json.loads(doc_i)
            anns_by_doccano_id = dict()
            # First convert entities, then relations, finally attributes
            # because new annotation identifier is needed
            text = doc_ann["text"]
            ch_sp=[m.start(0) for m in re.finditer("\r", text)]
            
            
            
            for doccano_ent in doc_ann["entities"]:
                nchar_less = sum(lim < doccano_ent["start_offset"] for lim in ch_sp)
                entity = Entity(
               
                    label=doccano_ent["label"],
                    spans=[Span(doccano_ent["start_offset"]+nchar_less,doccano_ent["end_offset"]+nchar_less)],
                    text=text[doccano_ent["start_offset"]:doccano_ent["end_offset"]],
                    
                )
                anns_by_doccano_id[doccano_ent["id"]] = entity
                if self._prov_tracer is not None:
                    self._prov_tracer.add_prov(
                        entity, self.description, source_data_items=[]
                    )
    
            for doccano_relation in doc_ann["relations"]:
                relation = Relation(
                    label=doccano_relation["type"],
                    source_id=anns_by_doccano_id[doccano_relation["from_id"]].uid,
                    target_id=anns_by_doccano_id[doccano_relation["to_id"]].uid,
                   
                )
                anns_by_doccano_id[relation.uid] = relation
                if self._prov_tracer is not None:
                    self._prov_tracer.add_prov(
                        relation, self.description, source_data_items=[]
                    )

            
            
            text_anns.append( {"text" : text, 
                                           "id": doc_ann["id"], 
                                           "anns" : list(anns_by_doccano_id.values())})
        return text_anns
