from django.db import connection


def bucket_and_name(path):
    if path.startswith("bags/"):
        path = path.split("/")[-1]
        return "bags", path
    elif path.startswith("tmp/"):
        bucket_and_path = path.split("/")
        return bucket_and_path[0], "/".join(bucket_and_path[1:])
    elif path.startswith("zips/"):
        bucket_and_path = path.split("/")
        return bucket_and_path[0], "/".join(bucket_and_path[1:])
    res_id = path.split("/")[0] if "/" in path else path
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
        owner_username_query = f'SELECT "theme_userprofile"."_bucket_name" \
                                FROM "theme_userprofile" \
                                WHERE "theme_userprofile"."user_id" = {owner_id}'
        cursor.execute(owner_username_query)
        row = cursor.fetchone()
        bucket_name = row[0]
    return bucket_name, path


def normalized_bucket_name(username):
    with connection.cursor() as cursor:
        user_id_from_username_query = f'SELECT "auth_user"."id" \
                                        FROM "auth_user" \
                                        WHERE "auth_user"."username" = {username}'
        cursor.execute(user_id_from_username_query)
        row = cursor.fetchone()
        if row is None:
            raise Exception(f"User with username {username} not found")
        owner_id = row[0]
        owner_username_query = f'SELECT "theme_userprofile"."_bucket_name" \
                                FROM "theme_userprofile" \
                                WHERE "theme_userprofile"."user_id" = {owner_id}'
        cursor.execute(owner_username_query)
        row = cursor.fetchone()
        bucket_name = row[0]
        return bucket_name
