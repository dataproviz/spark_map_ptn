from docling.document_converter import (
    DocumentConverter, WordFormatOption, PowerpointFormatOption
)
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import SimplePipelineOptions

# Shared options for both formats
simple_pipeline = SimplePipelineOptions(
    do_table_structure=True,
    do_picture_classif=False,
    do_picture_description=False,
    document_timeout=120 # Seconds - increase more
)

converter = DocumentConverter(
    format_options={
        InputFormat.DOCX: WordFormatOption(
            pipeline_options=simple_pipeline
        ),
        InputFormat.PPTX: PowerpointFormatOption(
            pipeline_options=simple_pipeline
        )
    }
)

# Converts all files — auto-routes to correct pipeline per format
results = converter.convert_all(["doc1.docx", "deck1.pptx", "doc2.docx"])