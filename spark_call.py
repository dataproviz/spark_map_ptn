from pyspark.sql.types import StructType, StructField, StringType, LongType

schema = StructType([
    StructField("path", StringType(), False),
    StructField("chunk_id", LongType(), False),
    StructField("text", StringType(), True),
    StructField("error", StringType(), True),
])

# DataFrame of file paths
df_paths = spark.createDataFrame(
    [("s3a://my-bucket/docs/file1.pdf",),
     ("s3a://my-bucket/docs/file2.docx",)],
    ["path"]
)

# Control parallelism explicitly
rdd = df_paths.repartition(200).rdd

chunks_df = spark.createDataFrame(
    rdd.mapPartitions(docling_map_partitions),
    schema
)

# Persist results
(chunks_df
 .write
 .mode("append")
 .format("delta")
 .saveAsTable("silver.doc_chunks"))