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
    resource_query = 'SELECT quota_holder_id \
                        FROM hs_core_genericresource \
                        WHERE short_id = %s'

    with connection.cursor() as cursor:
        cursor.execute(resource_query, [res_id])
        row = cursor.fetchone()
        if row is None:
            raise Exception(f"Resource with short_id {res_id} not found")
        owner_id = row[0]
        owner_username_query = 'SELECT _bucket_name \
                                FROM theme_userprofile WHERE user_id = %s'
    with connection.cursor() as cursor:
        cursor.execute(owner_username_query, [owner_id])
        row = cursor.fetchone()
        bucket_name = row[0]
    return bucket_name, path


def normalized_bucket_name(username):
    with connection.cursor() as cursor:
        user_id_from_username_query = 'SELECT id \
                                        FROM auth_user \
                                        WHERE username = %s'
        cursor.execute(user_id_from_username_query, [username])
        row = cursor.fetchone()
        if row is None:
            raise Exception(f"User with username {username} not found")
        owner_id = row[0]
        owner_username_query = 'SELECT _bucket_name \
                                FROM theme_userprofile \
                                WHERE user_id = %s'
        cursor.execute(owner_username_query, [owner_id])
        row = cursor.fetchone()
        bucket_name = row[0]
        return bucket_name


def is_metadata_xml_file(file_path):
    """Determine whether a given file is metadata.
    Note: this will return true for any file that ends with the metadata endings
    We are taking the risk that user might create a file with the same filename ending
    """
    from hs_file_types.enums import AggregationMetaFilePath

    if not (file_path.endswith(AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
            or file_path.endswith(AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)):
        return False
    return True
