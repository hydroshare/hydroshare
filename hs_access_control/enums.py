import enum


class CommunityRequestEvents(str, enum.Enum):
    CREATED = "created"
    DECLINED = "declined"
    APPROVED = "approved"


class CommunityRequestActions(str, enum.Enum):
    REQUEST = 'request'
    UPDATE = 'update'
    APPROVE = 'approve'
    DECLINE = 'decline'
    REMOVE = 'remove'
