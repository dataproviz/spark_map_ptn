import boto3
from datetime import datetime
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

def process_and_chunk(rows):
    converter = DocumentConverter()
    chunker   = HybridChunker()
    dynamodb  = boto3.resource("dynamodb", region_name="us-east-1")
    table     = dynamodb.Table("document_processing_status")

    prev_file        = None
    prev_chunk_count = 0

    def get_status(file_path):
        try:
            response = table.get_item(Key={"file_path": file_path})
            return response.get("Item", {}).get("status", None)
        except Exception:
            return None  # treat as not processed if DynamoDB read fails

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
        file_path = row["file_path"]
        source    = row["source"]

        try:
            # ── 1. Check if already chunked ───────────────────────
            existing_status = get_status(file_path)

            if existing_status == "success":
                print(f"⏭️  Skipping {file_path} — already chunked")
                continue  # skip to next file

            if existing_status == "error":
                print(f"🔄 Retrying {file_path} — previous attempt failed")
                # fall through → reprocess

            # ── 2. Convert ────────────────────────────────────────
            result = converter.convert(file_path)

            # ── 3. Entering chunk loop → update PREVIOUS file ─────
            if prev_file:
                update_dynamodb(
                    file_path   = prev_file["file_path"],
                    source      = prev_file["source"],
                    status      = "success",
                    chunk_count = prev_chunk_count
                )
                print(f"✅ Updated prev: {prev_file['file_path']} → {prev_chunk_count} chunks")

            # ── 4. Chunk current file ─────────────────────────────
            chunk_count = 0
            for chunk in chunker.chunk(result.document):
                chunk_count += 1
                yield {
                    "file_path":  file_path,
                    "source":     source,
                    "chunk_text": chunk.text,
                    "status":     "success"
                }

            # ── 5. Store current as previous for next iteration ───
            prev_file        = {"file_path": file_path, "source": source}
            prev_chunk_count = chunk_count

        except Exception as e:
            # ── Update previous file if exists ────────────────────
            if prev_file:
                update_dynamodb(
                    file_path   = prev_file["file_path"],
                    source      = prev_file["source"],
                    status      = "success",
                    chunk_count = prev_chunk_count
                )

            # ── Mark current file as error ────────────────────────
            update_dynamodb(
                file_path = file_path,
                source    = source,
                status    = "error",
                error     = str(e)
            )

            prev_file        = None
            prev_chunk_count = 0

            yield {
                "file_path":  file_path,
                "source":     source,
                "chunk_text": None,
                "status":     "error"
            }

    # ── Update LAST file after loop ends ──────────────────────────
    if prev_file:
        update_dynamodb(
            file_path   = prev_file["file_path"],
            source      = prev_file["source"],
            status      = "success",
            chunk_count = prev_chunk_count
        )
        print(f"✅ Updated last: {prev_file['file_path']} → {prev_chunk_count} chunks")


# ── Run ───────────────────────────────────────────────────────────
result_rdd = files_df.rdd.mapPartitions(process_and_chunk)
result_df  = spark.createDataFrame(result_rdd)
```

---

### Status-Based Routing
```
For each file
        │
        ├── status = "success" → ⏭️  Skip  (already done)
        ├── status = "error"   → 🔄 Retry  (previous attempt failed)
        └── status = None      → 🆕 Process (first time)