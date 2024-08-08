from hs_core.models import BaseResource
from django.contrib.auth.models import User


def bucket_and_name(path):
    res_id = "/".join(path.split("/")[:1])
    res = BaseResource.objects.get(short_id=res_id)
    owner: User = res.quota_holder
    key = "/".join(path.split("/")[1:])
    return owner.username, key