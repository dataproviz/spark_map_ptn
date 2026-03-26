import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('YourTableName')

def update_item(pk, sk, updates: dict):
    """
    updates = {'name': 'Siva Kumar', 'city': 'Dallas', 'status': 'active'}
    """
    update_expression = 'SET ' + ', '.join(f'#k{i} = :v{i}' for i in range(len(updates)))
    
    expression_attribute_names = {f'#k{i}': k for i, k in enumerate(updates.keys())}
    expression_attribute_values = {f':v{i}': v for i, v in enumerate(updates.values())}

    table.update_item(
        Key={'pk': pk, 'sk': sk},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )

# Usage
update_item(
    pk='USER#123',
    sk='PROFILE',
    updates={
        'name': 'Siva Kumar',
        'city': 'Dallas',
        'status': 'active'
    }
)
```

**What this builds dynamically:**
```
UpdateExpression:          SET #k0 = :v0, #k1 = :v1, #k2 = :v2
ExpressionAttributeNames:  {'#k0': 'name', '#k1': 'city', '#k2': 'status'}
ExpressionAttributeValues: {':v0': 'Siva Kumar', ':v1': 'Dallas', ':v2': 'active'}