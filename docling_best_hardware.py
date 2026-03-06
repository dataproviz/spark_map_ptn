from docling.document_converter import DocumentConverter, WordFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import SimplePipelineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice

# Auto-detect best hardware
accelerator_options = AcceleratorOptions(
    device=AcceleratorDevice.AUTO,  # CUDA → MPS → CPU
    num_threads=8                   # tune to your CPU core count
)

pipeline_options = SimplePipelineOptions(
    do_table_structure=True,
    do_picture_classif=False,
    do_picture_description=False,
    document_timeout=300
)

converter = DocumentConverter(
    accelerator_options=accelerator_options,
    format_options={
        InputFormat.DOCX: WordFormatOption(
            pipeline_options=pipeline_options
        )
    }
)
```

---

### AUTO Detection Priority
```
AcceleratorDevice.AUTO
        │
        ├── NVIDIA GPU (CUDA) available? → Use CUDA   (~8x faster)
        ├── Apple Silicon (MPS) available? → Use MPS  (~3x faster)
        └── Neither? → Fall back to CPU               (baseline)