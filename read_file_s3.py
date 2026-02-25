import boto3
import json
import io

s3_client = boto3.client('s3')

def read_json_from_s3(bucket: str, key: str) -> dict:
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = io.StringIO(response['Body'].read().decode('utf-8'))
    return json.load(content)

data = read_json_from_s3("my-bucket", "path/to/file.json")