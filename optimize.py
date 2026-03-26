from delta.tables import DeltaTable

dt = DeltaTable.forPath(spark, "/path/to/delta-table")

# After your batch OPTIMIZE + Z-ORDER
dt.optimize().where("os_status = 'INDEXED'").executeZOrderBy("tenant_id")
dt.vacuum(retentionHours=168)  # safe default, preserves 7-day time travel
