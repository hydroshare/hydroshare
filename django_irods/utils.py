

def bucket_and_name(path):
    from django.contrib.auth.models import User
    from hs_core.models import BaseResource

    if path.startswith("bags/"):
        path = path.split("/")[-1].strip(".zip")
    res_id = "/".join(path.split("/")[:1])
    res = BaseResource.objects.get(short_id=res_id)
    owner: User = res.quota_holder
    #key = "/".join(path.split("/")[1:])
    key = path
    return owner.username, key