import re
from django.db import connection


def bucket_and_name(path):
    res_id = "/".join(path.split("/")[:1])
    if path.startswith("bags/"):
        path = path.split("/")[-1]
        return "bags", path
    elif path.startswith("tmp/"):
        bucket_and_path = path.split("/")
        return bucket_and_path[0], "/".join(bucket_and_path[1:])
    elif path.startswith("zips/"):
        bucket_and_path = path.split("/")
        return bucket_and_path[0], "/".join(bucket_and_path[1:])
    resource_query = f'SELECT "pages_page"."id", "pages_page"."_order", "hs_core_genericresource"."short_id", \
                        "hs_core_genericresource"."quota_holder_id", "hs_core_genericresource"."page_ptr_id" \
                        FROM "hs_core_genericresource" \
                        INNER JOIN "pages_page" ON ("hs_core_genericresource"."page_ptr_id" = "pages_page"."id") \
                        WHERE "hs_core_genericresource"."short_id" = \'{res_id}\' ORDER BY "pages_page"."_order" ASC'

    with connection.cursor() as cursor:
        cursor.execute(resource_query)
        row = cursor.fetchone()
        if row is None:
            raise Exception(f"Resource with short_id {res_id} not found")
        owner_id = row[3]
        owner_username_query = f'SELECT "auth_user"."id", "auth_user"."username" \
                                 FROM "auth_user" WHERE "auth_user"."id" = {owner_id}'
        cursor.execute(owner_username_query)
        row = cursor.fetchone()
        owner_username = row[1]
    return _normalized_bucket_name(owner_username), path

def _normalized_bucket_name(username):
    # duplicate of theme.models.UserProfile.bucket_name property method
    # Cannot import theme.models.UserProfile due to circular import
    return re.sub("[^A-Za-z0-9\.-]", "", re.sub("[@]", ".at.", username.lower()))
