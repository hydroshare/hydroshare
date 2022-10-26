import enum


class CommunityRequestEvents(str, enum.Enum):
    CREATED = "created"
    DECLINED = "declined"
    APPROVED = "approved"
