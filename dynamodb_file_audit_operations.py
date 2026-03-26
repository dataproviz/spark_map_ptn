def is_file_processed(pk_value: str, sk_value: str) -> tuple:
    response = table.get_item(
        Key={
            "pk": pk_value,
            "sk": sk_value
        },
        ProjectionExpression="process_status"
    )
    if "Item" in response:
        return response["Item"]["process_status"] == "success"
    return False


def insert_file_audit(item_dict:dict):
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