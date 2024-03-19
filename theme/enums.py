import enum


class QuotaStatus(str, enum.Enum):
    """Quota status message type"""

    ENFORCEMENT = 'enforcement'
    GRACE_PERIOD = 'grace_period'
    WARNING = 'warning'
    INFO = 'info'
