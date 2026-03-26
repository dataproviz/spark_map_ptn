import boto3

# Connect to DynamoDB Local
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:8000",
    region_name="us-west-2",
    aws_access_key_id="111",
    aws_secret_access_key="111"
)

table = dynamodb.Table("my-audit")

insert_audit_entry = {
            "pk":"file_key",
            "sk":"run_id_1_docx",
            "file_key":   "file_key",

            "file_name": "file_name",
            "file_type":"docx",
            "file_size":0,

            "processor_type":"docling",
            "process_status": "starting",
            "file_key_hash":"file_key_hash",
            "file_checksum":"checksum",
}
def insert_file_audit(file_path, source, status, chunk_count=0, error=None):
    table.put_item(
        Item={
            "pk":"",
            "sk":"",
            "file_key":   "file_key",
            "file_key_hash":"file_key"
            "file_name": "file_name",
            "file_checksum":"checksum",
            "file_type":"docx",
            "processor_type":"ptype",
            "process_status":      status,


            "chunk_count": chunk_count,
            "updated_at":  datetime.utcnow().isoformat(),
            "created_at":  datetime.utcnow().isoformat(),
            "error_msg":       error,
            "error_traceback":"traceback"
        }
    )

def file_audit_exists(pk_value: str, sk_value: str) -> tuple:
    response = table.get_item(
        Key={
            "pk": pk_value,
            "sk": sk_value
        }
    )
    if "Item" in response:
        return True, response["Item"]["process_status"] == "success"
    return False, False

rec_exists, file_processed = file_audit_exists(table, "2026-03-10", "file_name1" )

if file_processed:
    continue
if !rec_exists:
    #create record - put items

print(file_audit_exists(table, "2026-03-10sss", "file_name1" ))