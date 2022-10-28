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


class CommunityActions(str, enum.Enum):
    OWNER = 'owner'
    INVITE = 'invite'
    APPROVE = 'approve'
    DECLINE = 'decline'
    REMOVE = 'remove'
    RETRACT = 'retract'
    DEACTIVATE = 'deactivate'
    ADD = 'add'
