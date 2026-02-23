def is_credentials_expiring_within_10_minutes(expiry_time):
    """Return True if credentials expire within 10 minutes or don't exist."""
    if expiry_time is None:
        logger.info("No credentials yet.")
        return True

    now            = datetime.now(timezone.utc)
    time_remaining = (expiry_time - now).total_seconds()

    logger.info("Credentials time remaining: %.0f seconds (%.1f minutes)",
                time_remaining, time_remaining / 60)

    if time_remaining <= 0:
        logger.warning("Credentials EXPIRED.")
        return True

    if time_remaining < EXPIRY_THRESHOLD_SECONDS:
        logger.warning("Credentials expiring within 10 minutes (%.1f min left) — renewing.",
                       time_remaining / 60)
        return True

    logger.info("Credentials valid for %.1f more minutes.", time_remaining / 60)
    return False