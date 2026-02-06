# One-liner
files = [
    f"s3://{bucket}/{obj['Key']}"
    for page in s3_client.get_paginator('list_objects_v2')
                         .paginate(Bucket='my-bucket', Prefix='docs/')
    for obj in page.get('Contents', [])
    if obj['Key'].endswith(('.pdf', '.docx'))
]