def build_in_clause(widget_name: str) -> str:
    """
    Reads a comma-separated text widget and returns
    a quoted SQL IN clause string.

    Usage:
        WHERE city IN ({build_in_clause("cities")})
    """
    raw    = dbutils.widgets.get(widget_name)
    values = [v.strip() for v in raw.split(",") if v.strip()]

    if not values:
        raise ValueError(f"Widget '{widget_name}' has no valid values")

    return ", ".join([f"'{v}'" for v in values])


# Use in any query
query = f"""
    SELECT *
    FROM   people
    WHERE  address.city IN ({build_in_clause("cities")})
    AND    environment  IN ({build_in_clause("environments")})
    AND    role_name    IN ({build_in_clause("role_names")})
"""

spark.sql(query).show(truncate=False)