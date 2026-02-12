def process_with_stable_chunk_ids(partition):
    """
    Generate stable chunk IDs that don't rely solely on index
    """
    import boto3
    import tempfile
    import os
    import json
    import hashlib
    from docling.document_converter import DocumentConverter
    from docling.chunking import HybridChunker
    
    s3_client = boto3.client('s3')
    converter = DocumentConverter()
    
    chunker = HybridChunker(
        tokenizer="amazon.titan-embed-text-v1",
        max_tokens=512,
        merge_peers=True
    )
    
    for row in partition:
        file_id = row.file_id
        bucket = row.bucket
        key = row.key
        file_type = row.file_type
        temp_file = None
        
        try:
            # Download and convert
            suffix = f'.{file_type}'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                temp_file = tmp.name
            
            s3_client.download_file(bucket, key, temp_file)
            
            # Get file metadata for versioning
            file_metadata = s3_client.head_object(Bucket=bucket, Key=key)
            file_etag = file_metadata['ETag'].strip('"')
            last_modified = str(file_metadata['LastModified'])
            
            result = converter.convert(temp_file)
            doc = result.document
            
            # Create chunks
            chunk_iter = chunker.chunk(dl_doc=doc)
            
            for idx, chunk in enumerate(chunk_iter):
                chunk_text = chunk.text
                
                # Create multiple ID strategies
                
                # 1. Simple index-based ID
                index_id = f"{file_id}_{idx}"
                
                # 2. Content hash-based ID (stable across re-processing)
                content_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()[:16]
                hash_id = f"{file_id}_{content_hash}"
                
                # 3. Composite ID with file version
                versioned_id = f"{file_id}_{file_etag}_{idx}"
                
                # 4. Position-based ID (first N chars as fingerprint)
                position_fingerprint = hashlib.md5(chunk_text[:100].encode('utf-8')).hexdigest()[:8]
                position_id = f"{file_id}_{idx}_{position_fingerprint}"
                
                yield (
                    file_id,
                    f's3://{bucket}/{key}',
                    file_type,
                    'success',
                    idx,  # Original index
                    index_id,  # Simple ID
                    hash_id,  # Content-based ID
                    versioned_id,  # Version-aware ID
                    position_id,  # Position-aware ID
                    chunk_text,
                    json.dumps({
                        'file_etag': file_etag,
                        'last_modified': last_modified,
                        'token_count': len(chunk_text.split()),
                        'char_count': len(chunk_text),
                        'content_hash': content_hash
                    }),
                    None
                )
        
        except Exception as e:
            yield (
                file_id,
                f's3://{bucket}/{key}',
                file_type,
                'failed',
                None, None, None, None, None, None, None,
                str(e)
            )
        
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass

# Schema with multiple ID strategies
stable_id_schema = StructType([
    StructField("file_id", StringType()),
    StructField("file_path", StringType()),
    StructField("file_type", StringType()),
    StructField("status", StringType()),
    StructField("chunk_index", IntegerType()),
    StructField("chunk_id_simple", StringType()),
    StructField("chunk_id_hash", StringType()),
    StructField("chunk_id_versioned", StringType()),
    StructField("chunk_id_position", StringType()),
    StructField("chunk_text", StringType()),
    StructField("chunk_metadata", StringType()),
    StructField("error", StringType())
])