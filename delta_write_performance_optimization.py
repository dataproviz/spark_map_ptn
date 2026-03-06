# Set configs once at session level
spark.conf.set("spark.sql.adaptive.execution.enabled",              "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled",     "true")
spark.conf.set("spark.sql.shuffle.partitions",                      "8")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled",      "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled",        "true")

# Write with optimal partitioning
df.repartition(8, "source") \
    .write \
    .format("delta") \
    .mode("append") \
    .partitionBy("source") \
    .save("/path/to/delta")
##################################################
# Let Delta auto-optimize file sizes during write
df.write \
    .format("delta") \
    .option("delta.autoOptimize.optimizeWrite", "true") \
    .option("delta.autoOptimize.autoCompact",   "true") \
    .mode("append") \
    .partitionBy("source") \
    .save("/path/to/delta")
#--------------------------------------------


#####
from delta.tables import DeltaTable

delta_table = DeltaTable.forPath(spark, "/path/to/delta")

# Compact all small files into larger ones
delta_table.optimize().executeCompaction()

# Z-Order for faster reads on frequent filter columns
delta_table.optimize().executeZOrderBy("source", "doc_type")