from datetime import datetime, timezone

def utc_now():
    """Timezone-aware replacement for datetime.utcnow() which is deprecated."""
    return datetime.now(timezone.utc)
