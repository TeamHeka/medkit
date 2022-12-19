# Make your own module

Here is a tutorial for developing your own operation module.
For more information, you can refer to [API documentation](api:core:operations).

## 1. Creating your class

We have defined several abstract classes you can use as parent class.
You can find several examples of implemented modules in [medkit.text](../api/text).

For all operations inheriting from `Operation` abstract class, these 4 lines
shall be added in `__init__` method:
```
def __init__(self, ..., uid=None):
    ...
    # Pass all arguments to super (remove self)
    init_args = locals()
    init_args.pop("self")
    super().__init__(**init_args)
```

Here is an example of a custom segmentation module:
```
class MyTokenizer(SegmentationOperation):

    def __init__(
        self,
        output_label,
        ...
        uid = None,
    ):
        # Pass all arguments to super (remove self)
        init_args = locals()
        init_args.pop("self")
        super().__init__(**init_args)

        ...

        self.output_label = output_label
```

## 2. Implement the `run` method

There are different existing abstract classes which define the operation inputs
and outputs according the nature of the operation.

For example, a segmentation module requires a list of segments as input and
returns a new list of segments.

Here is an example of an implementation of our tokenizer. It uses a private 
method which processes each segment to return a list of tokens for this 
segment.

```
class MyTokenizer(SegmentationOperation):
    ...
    def run(self, segments: List[Segment]) -> List[Segment]:
        # Here is your code for the tokenizer:
        # * process each input
        return [
            token
            for segment in segments
            for token in self._mytokenmethod(segment) 
```

## 3. Make your operation non-destructive (for text)

To ensure that all extracted information correspond to a part of original 
text, each annotation holds a list of spans. This spans correspond to the 
location in the raw document.

For more information, you can refer to [API documentation](api:core-text:span).
A set of utils functions have been implemented to help you to keep span 
information all along your processing pipeline.

An example of the functions' usage is available [here](../examples/spans).

Here is an example of our tokenizer which role is to cut the segment in two 
segments.

```
class MyTokenizer(SegmentationOperation):
    ...
    def _mytokenmethod(self, segment):
        # process the segment (e.g., cut the segment)
        size = len(segment)
        cut_index = size // 2
        # extract spans and create segment annotations
        # 1st part
        text, spans = span_utils.extract(
            text=segment.text,
            spans=segment.spans,
            ranges=[(0, cut_index)]
        )
        new_segment1 = Segment(
            label=self.output_label,
            spans=spans,
            text=text,
       ) 
        # 2nd part
        text, spans = span_utils.extract(
            text=segment.text,
            spans=segment.spans,
            ranges=[(cut_index, size)]
        )
        new_segment2 = Segment(
            label=self.output_label,
            spans=spans,
            text=text,
       ) 

       ...

        # Returns new segments
        return (new_segment1, new_segment2)
```

## 4. Make your operation support data provenance tracing

Data provenance is a core concept of medkit.
It ensures the traceability of the extracted information by providing the 
set of operations which allow to infer this information and also the 
sequence of data used for it.

The `Operation` abstract class allows to set underlying the mechanism for 
your own operation but you are the only one who knows which information 
needs to be stored. 

For more information, you can refer to [API documentation](api:core:provenance).

Here is our example which store information about:
* the item produced
* which operation produces it (i.e., MyTokenizer)
* the source item which has been processed

```
class MyTokenizer(SegmentationOperation):
    ...
    def _mytokenmethod(self, segment):
        ...
        
        # save the provenance data for this operation
        if self._prov_tracer is not None:
            self._prov_tracer.add_prov(
                data_item=new_segment1,
                op_desc=self.description,
                source_data_items= [segment]
            )
        if self._prov_tracer.add_prov(
                data_item=new_segment2,
                op_desc=self.description,
                source_data_items= [segment]
            )

        # Returns new segments
        return (new_segment1, new_segment2)
```
``
