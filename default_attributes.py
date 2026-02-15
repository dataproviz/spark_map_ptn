# Method 3: Dictionary-based configuration
DEFAULT_CONFIG = {
    "environment": "dev",
    "database": "my_local_db",
    "table_name": "my_table",
    "batch_size": "1000"
}

config = {}
for param, default_value in DEFAULT_CONFIG.items():
    config[param] = dbutils.widgets.getArgument(param, default_value)

# Use the config
print(f"Running with environment: {config['environment']}")
spark.sql(f"USE {config['database']}")