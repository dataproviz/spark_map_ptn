def generate_robust_chunk_id(file_id, chunk_index, chunk_text, file_version):
    """
    Generate a robust chunk ID that works for updates and re-processing
    
    Format: {file_id}_{version}_{index}_{content_hash}
    """
    import hashlib
    
    # Short content hash for collision detection
    content_hash = hashlib.sha256(chunk_text.encode('utf-8')).hexdigest()[:12]
    
    # Composite ID
    chunk_id = f"{file_id}_{file_version}_{chunk_index}_{content_hash}"
    
    return chunk_id

def process_with_robust_ids(partition):
    """
    Production-ready chunk processing with robust IDs
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
            # Get file version (ETag or version ID)
            file_metadata = s3_client.head_object(Bucket=bucket, Key=key)
            file_version = file_metadata['ETag'].strip('"')[:8]  # First 8 chars of ETag
            
            # Download and convert
            suffix = f'.{file_type}'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                temp_file = tmp.name
            
            s3_client.download_file(bucket, key, temp_file)
            
            result = converter.convert(temp_file)
            doc = result.document
            
            # Create chunks
            chunk_iter = chunker.chunk(dl_doc=doc)
            
            for idx, chunk in enumerate(chunk_iter):
                chunk_text = chunk.text
                
                # Generate robust ID
                chunk_id = generate_robust_chunk_id(
                    file_id, 
                    idx, 
                    chunk_text, 
                    file_version
                )
                
                yield (
                    file_id,
                    chunk_id,  # Use this as primary key
                    f's3://{bucket}/{key}',
                    file_type,
                    file_version,
                    idx,
                    chunk_text,
                    'success',
                    None
                )
        
        except Exception as e:
            yield (file_id, None, f's3://{bucket}/{key}', file_type, None, None, None, 'failed', str(e))
        
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass