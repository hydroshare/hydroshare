import enum


class QuotaStatus(str, enum.Enum):
    """Quota status message type"""

    ENFORCEMENT = 'enforcement'
    WARNING = 'warning'
    INFO = 'info'
