def process_and_chunk(rows):
    converter = DocumentConverter()
    chunker   = HybridChunker()
    dynamodb  = boto3.resource("dynamodb", region_name="us-east-1")
    table     = dynamodb.Table("document_processing_status")

    def update_dynamodb(file_path, source, status, chunk_count=0, error=None):
        table.put_item(
            Item={
                "file_path":   file_path,
                "source":      source,
                "status":      status,
                "chunk_count": chunk_count,
                "updated_at":  datetime.utcnow().isoformat(),
                "error":       error
            }
        )

    for row in rows:
        file_path   = row["file_path"]
        source      = row["source"]
        chunk_count = 0

        try:
            result = converter.convert(file_path)

            # ── Yield each chunk one by one ───────────────────────
            for chunk in chunker.chunk(result.document):
                chunk_count += 1
                yield {
                    "file_path":  file_path,
                    "source":     source,
                    "chunk_text": chunk.text,
                    "status":     "success"
                }

            # ── No more chunks → update DynamoDB as success ───────
            update_dynamodb(
                file_path   = file_path,
                source      = source,
                status      = "success",
                chunk_count = chunk_count
            )
            print(f"✅ {file_path} → {chunk_count} chunks")

        except Exception as e:
            update_dynamodb(
                file_path = file_path,
                source    = source,
                status    = "error",
                error     = str(e)
            )
            yield {
                "file_path":  file_path,
                "source":     source,
                "chunk_text": None,
                "status":     "error"
            }
```

---

### Why This Works
```
File 1:
  yield chunk 1  ──→ caller receives chunk 1
  yield chunk 2  ──→ caller receives chunk 2
  yield chunk 3  ──→ caller receives chunk 3
  no more chunks ──→ inner for loop exits naturally
  table.put_item ──→ ✅ DynamoDB updated as success
  
File 2:
  yield chunk 1  ──→ caller receives chunk 1
  ...
```

The inner `for chunk` loop **always exits cleanly** when chunks are exhausted — execution falls through to `table.put_item()` exactly when you want it.

---

### Execution Flow
```
chunker.chunk() exhausted?
        │
        YES → inner for loop exits
            → table.put_item(status="success") ✅
            → outer loop moves to next file
        │
        NO  → yield next chunk → suspended → resume on next call