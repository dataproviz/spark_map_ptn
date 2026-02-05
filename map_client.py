import os
import tempfile
from urllib.parse import urlparse
from pyspark.sql import Row

def _parse_s3_url(url: str):
    # Accept s3a://bucket/key or s3://bucket/key
    url = url.replace("s3a://", "s3://", 1)
    u = urlparse(url)
    if u.scheme != "s3" or not u.netloc:
        raise ValueError(f"Not an S3 URL: {url}")
    return u.netloc, u.path.lstrip("/")

def docling_map_partitions_boto3(rows_iter):
    # Imports inside executor
    import boto3
    from botocore.config import Config
    from docling.document_converter import DocumentConverter
    from docling.chunking import HybridChunker

    # One client per partition (important)
    s3 = boto3.client(
        "s3",
        config=Config(
            retries={"max_attempts": 10, "mode": "standard"},
            max_pool_connections=50,
        ),
    )

    converter = DocumentConverter()  # once per partition
    chunker = HybridChunker()        # once per partition

    BUF = 16 * 1024 * 1024  # 16MB

    for r in rows_iter:
        # r can be Row or dict depending on how you built the RDD
        path = r["path"] if isinstance(r, dict) else r.path

        try:
            bucket, key = _parse_s3_url(path)

            with tempfile.TemporaryDirectory() as td:
                local_file = os.path.join(td, os.path.basename(key) or "doc.bin")

                # Stream S3 -> local file (no full file in RAM)
                resp = s3.get_object(Bucket=bucket, Key=key)
                body = resp["Body"]
                try:
                    with open(local_file, "wb") as out:
                        for chunk in iter(lambda: body.read(BUF), b""):
                            out.write(chunk)
                finally:
                    body.close()

                # Docling parse + chunk
                result = converter.convert(local_file, raises_on_error=False)
                if result.document is None:
                    yield Row(path=path, chunk_id=0, text=None, error="Docling returned no document")
                    continue

                for i, ch in enumerate(chunker.chunk(result.document)):
                    yield Row(path=path, chunk_id=int(i), text=chunker.contextualize(ch), error=None)

        except Exception as e:
            yield Row(path=path, chunk_id=0, text=None, error=str(e))
