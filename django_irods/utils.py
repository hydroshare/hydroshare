from django.db import connection


def bucket_and_name(path):
    if path.startswith("bags/"):
        path = path.split("/")[-1].strip(".zip")
    res_id = "/".join(path.split("/")[:1])
    resource_query = f'SELECT "pages_page"."id", "pages_page"."_order", "hs_core_genericresource"."short_id", \
                        "hs_core_genericresource"."quota_holder_id", "hs_core_genericresource"."page_ptr_id" \
                        FROM "hs_core_genericresource" \
                        INNER JOIN "pages_page" ON ("hs_core_genericresource"."page_ptr_id" = "pages_page"."id") \
                        WHERE "hs_core_genericresource"."short_id" = \'{res_id}\' ORDER BY "pages_page"."_order" ASC'

    with connection.cursor() as cursor:
        cursor.execute(resource_query)
        row = cursor.fetchone()
        owner_id = row[3]
        owner_username_query = f'SELECT "auth_user"."id", "auth_user"."username" \
                                 FROM "auth_user" WHERE "auth_user"."id" = {owner_id}'
        cursor.execute(owner_username_query)
        row = cursor.fetchone()
        owner_username = row[1]
    return owner_username, path
