source_value = "my_source"

df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("replaceWhere", f"source = '{source_value}'") \
    .partitionBy("source") \
    .save("/path/to/delta/table")