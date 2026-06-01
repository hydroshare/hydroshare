from django.contrib.auth.models import User, Group
from hs_access_control.models import PrivilegeCodes


def make_owner(user_id=11, group_id=250):
    """
    Make the user with the given user_id an owner of the group with the given group_id.
    """
    user = User.objects.get(id=user_id)
    admin_user = User.objects.get(id=3569)
    group = Group.objects.get(id=group_id)
    admin_user.uaccess.share_group_with_user(group, user, PrivilegeCodes.OWNER)
