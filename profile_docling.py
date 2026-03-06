from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter

settings.debug.profile_pipeline_timings = True

converter = DocumentConverter()
result = converter.convert("large_document.docx")

# This tells you exactly where time is spent
print(result.timings)
```

Sample output:
```
{
  "doc_load":          0.5s,   # XML parsing
  "table_structure":   2.1s,   # Table processing
  "picture_classif":  18.3s,   # ← bottleneck if images present
  "total":            21.2s
}