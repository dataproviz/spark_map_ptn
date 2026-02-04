def docling_map_partitions(rows_iter):
    # Heavy imports INSIDE executor
    from docling.document_converter import DocumentConverter
    from docling.chunking import HybridChunker

    converter = DocumentConverter()   # ONCE per partition
    chunker = HybridChunker()         # ONCE per partition

    for row in rows_iter:
        s3_path = row["path"]

        try:
            with tempfile.TemporaryDirectory() as td:
                local_file = os.path.join(
                    td, os.path.basename(s3_path) or "doc.bin"
                )

                # Stream S3 object to local disk
                stream_s3a_to_local(s3_path, local_file)

                # Convert document
                result = converter.convert(local_file, raises_on_error=False)
                if result.document is None:
                    yield (s3_path, 0, None, "Docling returned no document")
                    continue

                doc = result.document

                # Emit chunks
                for i, ch in enumerate(chunker.chunk(doc)):
                    text = chunker.contextualize(ch)
                    yield (s3_path, i, text, None)

        except Exception as e:
            # One file fails → emit error row, not job failure
            yield (s3_path, 0, None, str(e))