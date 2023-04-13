import enum


class CommunityRequestEvents(enum.Enum):
    """Enum object for naming various events related to request for creating a new community"""

    CREATED = enum.auto()
    DECLINED = enum.auto()
    APPROVED = enum.auto()
    RESUBMITTED = enum.auto()


class CommunityGroupEvents(enum.Enum):
    """Enum object for naming various events related to actions on a group requesting to join a community"""

    DECLINED = enum.auto()
    APPROVED = enum.auto()
    INVITED = enum.auto()
    JOIN_REQUESTED = enum.auto()


class CommunityJoinRequestTypes(enum.Enum):
    """Enum object for naming request/invite for a group to join a community"""

    GROUP_REQUESTING = enum.auto()
    COMMUNITY_INVITING = enum.auto()


class CommunityRequestActions(str, enum.Enum):
    """Enum object for naming all allowed actions on a request to create a new community"""

    REQUEST = 'request'
    UPDATE = 'update'
    APPROVE = 'approve'
    DECLINE = 'decline'
    REMOVE = 'remove'
    CANCEL = 'cancel'
    RESUBMIT = 'resubmit'


class CommunityActions(str, enum.Enum):
    """Enum object for naming all allowed actions related to group joining a community"""
    OWNER = 'owner'
    INVITE = 'invite'
    APPROVE = 'approve'
    DECLINE = 'decline'
    REMOVE = 'remove'
    RETRACT = 'retract'
    DEACTIVATE = 'deactivate'
    ADD = 'add'
    JOIN = 'join'
    LEAVE = 'leave'
