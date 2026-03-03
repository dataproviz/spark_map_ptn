import boto3
import json
from botocore.exceptions import ClientError
from pyspark.sql import Row
from urllib.parse import urlparse

def check_s3_and_json(partition):
    s3_client = boto3.client('s3')
    
    # Configuration for your specific JSON check
    TARGET_FIELD = "status"      # The key in your JSON
    EXPECTED_VALUE = "active"    # The value you are looking for
    
    def get_s3_info_v2(uri):
        """Helper to check if file exists and get its size."""
        if not uri:
            return False, 0
        try:
            parsed = urlparse(uri)
            bucket = parsed.netloc
            key = parsed.path.lstrip('/')
            
            response = s3_client.head_object(Bucket=bucket, Key=key)
            return True, response.get('ContentLength', 0)
        except ClientError as e:
            # 404 means the file was not found
            return False, 0
        except Exception:
            return False, 0
        
    def get_s3_info(uri):
        """Checks existence and size (Metadata only)."""
        if not uri: return False, 0
        try:
            parsed = urlparse(uri)
            response = s3_client.head_object(Bucket=parsed.netloc, Key=parsed.path.lstrip('/'))
            return True, response.get('ContentLength', 0)
        except:
            return False, 0

    def validate_json_field(uri, field_name, expected_val):
        """Downloads JSON and checks if a field matches a value."""
        if not uri: return False
        try:
            parsed = urlparse(uri)
            # Fetch the actual content of the JSON file
            response = s3_client.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip('/'))
            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)
            
            # Check if the field exists and matches
            return data.get(field_name) == expected_val
        except:
            return False

    for row in partition:
        # 1. Check if files exist and are not empty
        s3_exists, s3_size = get_s3_info(row.s3_uri)
        meta_exists, meta_size = get_s3_info(row.metadata_s3_uri)
        
        # 2. Perform the specific JSON value check
        # (Only if the metadata file exists and isn't empty)
        json_value_match = False
        if meta_exists and meta_size > 0:
            json_value_match = validate_json_field(row.metadata_s3_uri, TARGET_FIELD, EXPECTED_VALUE)

        # 3. Aggregate results
        # Success = Exists, Not Empty, AND JSON field matches
        overall_status = "SUCCESS" if (s3_exists and s3_size > 0 and json_value_match) else "FAIL"
        
        yield Row(
            **row.asDict(),
            s3_valid=(s3_exists and s3_size > 0),
            json_match=json_value_match,
            final_check_result=overall_status
        )

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("S3Check").getOrCreate()

# Example Data
data = [
    ("s3://my-bucket/file1.csv", "s3://my-bucket/file1.json", "csv", "file1"),
    ("s3://my-bucket/empty.csv", "s3://my-bucket/missing.json", "csv", "file2")
]
columns = ["s3_uri", "metadata_s3_uri", "file_extension", "file"]
df = spark.createDataFrame(data, columns)

# Execute mapPartitions
# We use rdd.mapPartitions and then convert back to DF
checked_df = df.rdd.mapPartitions(check_s3_files).toDF()

checked_df.show()