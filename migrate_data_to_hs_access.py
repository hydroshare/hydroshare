import psycopg2
import psycopg2.extras
import sys
import uuid

con1 = None
con2 = None

if len(sys.argv) != 4:
    print "3 parameters have to be passed in to run this script: python migrate_data_to_hs_access.py DjangoDB_pwd HSAccessDB_pwd iRODS_cwd_path"
    exit(1)

try:
    # connect to Django db
    con1 = psycopg2.connect(database='postgres', user='postgres', password=sys.argv[1], host='postgis', port=5432)
    cur1 = con1.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # connect to HSAccess db
    con2 = psycopg2.connect(database='HSAccess', user='postgres', password=sys.argv[2], host='postgis', port=5432)
    cur2 = con2.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # retrieve all users from Django db and insert them into HSAccess db
    cur1.execute('SELECT username, is_staff, is_active from auth_user where username != \'root\'')
    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            if row['username']!='admin':
                user_uuid = uuid.uuid4().hex
                cur2.execute("""insert into users values (DEFAULT, %s, %s, %s, %s, %s, %s, DEFAULT)""",
                               (user_uuid, row['username'], 'HydroShare User', row['is_active'], row['is_staff'], 1))
                con2.commit()

    # retrieve all generic resources from Django db and insert them into HSAccess db
    cur1.execute('select auth_user.username, short_id, hs_core_title.value, public, frozen, do_not_distribute, '
                 'discoverable, published_and_frozen from hs_core_genericresource, auth_user, hs_core_title '
                 'where auth_user.username != \'root\' and hs_core_genericresource.user_id=auth_user.id '
                 'and hs_core_genericresource.object_id=hs_core_title.object_id '
                 'and hs_core_genericresource.content_type_id=hs_core_title.content_type_id')
    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            resource_path = sys.argv[3]+"/"+resource_uuid
            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (row['username'],))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % row['username']
                sys.exit(1)

            uid = cur2.fetchone()['user_id']
            cur2.execute("""insert into resources values (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT)""",
                       (resource_uuid, resource_path, row['value'],
                        row['frozen'], row['published_and_frozen'],
                        row['discoverable'], row['public'],
                        not row['do_not_distribute'], uid))
            con2.commit()

    # retrieve all generic resources owner permissions from Django db and insert them into HSAccess db
    cur1.execute('select hs_core_genericresource.short_id, auth_user.username from hs_core_genericresource_owners, hs_core_genericresource, auth_user '
                 'where auth_user.username != \'root\' and hs_core_genericresource_owners.genericresource_id=hs_core_genericresource.page_ptr_id '
                 'and hs_core_genericresource_owners.user_id=auth_user.id')
    print "rowcount of genericresource owners: ", cur1.rowcount
    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']
            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='own'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                   (uid, res_id, privilege_id, uid))
            con2.commit()

    # retrieve all generic resources edit_users permissions from Django db and insert them into HSAccess db
    cur1.execute('select hs_core_genericresource.short_id, auth_user.username from hs_core_genericresource_edit_users, hs_core_genericresource, auth_user '
                 'where auth_user.username != \'root\' and hs_core_genericresource_edit_users.genericresource_id=hs_core_genericresource.page_ptr_id '
                 'and hs_core_genericresource_edit_users.user_id=auth_user.id')
    print "rowcount of genericresource edit_users:", cur1.rowcount
    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='rw'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            # only insert into user_access_to_resource when the owner privilege is not already inserted
            # this check is needed to remove a wrong previous implementation that adds all owners into edit_users and view_users tables
            cur2.execute("""select privilege_id from user_access_to_resource where user_id=%s
                        and resource_id=%s and assertion_user_id=%s""", (uid, res_id, uid))
            if cur2.rowcount <= 0:
                cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                       (uid, res_id, privilege_id, uid))
                con2.commit()

    # retrieve all generic resources view_users permissions from Django db and insert them into HSAccess db
    cur1.execute('select hs_core_genericresource.short_id, auth_user.username from hs_core_genericresource_view_users, hs_core_genericresource, auth_user '
                 'where auth_user.username != \'root\' and hs_core_genericresource_view_users.genericresource_id=hs_core_genericresource.page_ptr_id '
                 'and hs_core_genericresource_view_users.user_id=auth_user.id')
    print "rowcount of genericresource view_users:", cur1.rowcount
    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='ro'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            # only insert into user_access_to_resource when the owner privilege is not already inserted
            # this check is needed to remove a wrong previous implementation that adds all owners into edit_users and view_users tables
            cur2.execute("""select privilege_id from user_access_to_resource where user_id=%s
                        and resource_id=%s and assertion_user_id=%s""", (uid, res_id, uid))
            if cur2.rowcount <= 0:
                cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                       (uid, res_id, privilege_id, uid))
                con2.commit()

    # retrieve all geographic raster resources from Django db and insert them into HSAccess db
    cur1.execute('select auth_user.username, short_id, hs_core_title.value, public, frozen, do_not_distribute, '
                 'discoverable, published_and_frozen from hs_geo_raster_resource_rasterresource, auth_user, hs_core_title '
                 'where auth_user.username != \'root\' and hs_geo_raster_resource_rasterresource.user_id=auth_user.id '
                 'and hs_geo_raster_resource_rasterresource.object_id=hs_core_title.object_id '
                 'and hs_geo_raster_resource_rasterresource.content_type_id=hs_core_title.content_type_id')
    print "rowcount of raster resources: ", cur1.rowcount
    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            resource_path = sys.argv[1]+"/"+resource_uuid
            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (row['username'],))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % row['username']
                sys.exit(1)

            uid = cur2.fetchone()['user_id']
            cur2.execute("""insert into resources values (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT)""",
                       (resource_uuid, resource_path, row['value'],
                        row['frozen'], row['published_and_frozen'],
                        row['discoverable'], row['public'],
                        not row['do_not_distribute'], uid))
            con2.commit()

    # retrieve all raster resources owner permissions from Django db and insert them into HSAccess db
    cur1.execute('select hs_geo_raster_resource_rasterresource.short_id, auth_user.username from hs_geo_raster_resource_rasterresource_owners, hs_geo_raster_resource_rasterresource, auth_user '
                 'where auth_user.username != \'root\' and hs_geo_raster_resource_rasterresource_owners.rasterresource_id=hs_geo_raster_resource_rasterresource.page_ptr_id '
                 'and hs_geo_raster_resource_rasterresource_owners.user_id=auth_user.id')

    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='own'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                   (uid, res_id, privilege_id, uid))
            con2.commit()

    # retrieve all raster resources edit_users permissions from Django db and insert them into HSAccess db
    cur1.execute('select hs_geo_raster_resource_rasterresource.short_id, auth_user.username from hs_geo_raster_resource_rasterresource_edit_users, hs_geo_raster_resource_rasterresource, auth_user '
                 'where auth_user.username != \'root\' and hs_geo_raster_resource_rasterresource_edit_users.rasterresource_id=hs_geo_raster_resource_rasterresource.page_ptr_id '
                 'and hs_geo_raster_resource_rasterresource_edit_users.user_id=auth_user.id')

    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='rw'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            # only insert into user_access_to_resource when the owner privilege is not already inserted
            # this check is needed to remove a wrong previous implementation that adds all owners into edit_users and view_users tables
            cur2.execute("""select privilege_id from user_access_to_resource where user_id=%s
                        and resource_id=%s and assertion_user_id=%s""", (uid, res_id, uid))
            if cur2.rowcount <= 0:
                cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                       (uid, res_id, privilege_id, uid))
                con2.commit()

    # retrieve all raster resources view_users permissions from Django db and insert them into HSAccess db
    cur1.execute('select hs_geo_raster_resource_rasterresource.short_id, auth_user.username from hs_geo_raster_resource_rasterresource_view_users, hs_geo_raster_resource_rasterresource, auth_user '
                 'where auth_user.username != \'root\' and hs_geo_raster_resource_rasterresource_view_users.rasterresource_id=hs_geo_raster_resource_rasterresource.page_ptr_id '
                 'and hs_geo_raster_resource_rasterresource_view_users.user_id=auth_user.id')

    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='ro'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            # only insert into user_access_to_resource when the owner privilege is not already inserted
            # this check is needed to remove a wrong previous implementation that adds all owners into edit_users and view_users tables
            cur2.execute("""select privilege_id from user_access_to_resource where user_id=%s
                        and resource_id=%s and assertion_user_id=%s""", (uid, res_id, uid))
            if cur2.rowcount <= 0:
                cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                       (uid, res_id, privilege_id, uid))
                con2.commit()

    # retrieve all ref_ts resources from Django db and insert them into HSAccess db
    cur1.execute('select auth_user.username, short_id, hs_core_title.value, public, frozen, do_not_distribute, '
                 'discoverable, published_and_frozen from ref_ts_reftimeseries, auth_user, hs_core_title '
                 'where auth_user.username != \'root\' and ref_ts_reftimeseries.user_id=auth_user.id and ref_ts_reftimeseries.object_id=hs_core_title.object_id '
                 'and ref_ts_reftimeseries.content_type_id=hs_core_title.content_type_id')
    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            resource_path = sys.argv[1]+"/"+resource_uuid
            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (row['username'],))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % row['username']
                sys.exit(1)

            uid = cur2.fetchone()['user_id']
            cur2.execute("""insert into resources values (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT)""",
                       (resource_uuid, resource_path, row['value'],
                        row['frozen'], row['published_and_frozen'],
                        row['discoverable'], row['public'],
                        not row['do_not_distribute'], uid))
            con2.commit()

    # retrieve all ref_ts resources owner permissions from Django db and insert them into HSAccess db
    cur1.execute('select ref_ts_reftimeseries.short_id, auth_user.username from ref_ts_reftimeseries_owners, ref_ts_reftimeseries, auth_user '
                 'where ref_ts_reftimeseries_owners.reftimeseries_id=ref_ts_reftimeseries.page_ptr_id and ref_ts_reftimeseries_owners.user_id=auth_user.id')

    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='own'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                   (uid, res_id, privilege_id, uid))
            con2.commit()

    # retrieve all ref_ts resources edit_users permissions from Django db and insert them into HSAccess db
    cur1.execute('select ref_ts_reftimeseries.short_id, auth_user.username from ref_ts_reftimeseries_edit_users, ref_ts_reftimeseries, auth_user '
                 'where auth_user.username != \'root\' and ref_ts_reftimeseries_edit_users.reftimeseries_id=ref_ts_reftimeseries.page_ptr_id '
                 'and ref_ts_reftimeseries_edit_users.user_id=auth_user.id')

    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='rw'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

            # only insert into user_access_to_resource when the owner privilege is not already inserted
            # this check is needed to remove a wrong previous implementation that adds all owners into edit_users and view_users tables
            cur2.execute("""select privilege_id from user_access_to_resource where user_id=%s
                        and resource_id=%s and assertion_user_id=%s""", (uid, res_id, uid))
            if cur2.rowcount <= 0:
                cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                       (uid, res_id, privilege_id, uid))
                con2.commit()

    # retrieve all ref_ts resources view_users permissions from Django db and insert them into HSAccess db
    cur1.execute('select ref_ts_reftimeseries.short_id, auth_user.username from ref_ts_reftimeseries_view_users, ref_ts_reftimeseries, auth_user '
                 'where auth_user.username != \'root\' and ref_ts_reftimeseries_view_users.reftimeseries_id=ref_ts_reftimeseries.page_ptr_id '
                 'and ref_ts_reftimeseries_view_users.user_id=auth_user.id')

    if cur1.rowcount > 0:
        rows = cur1.fetchall()
        for row in rows:
            resource_uuid = row['short_id']
            uname = row['username']

            # get user id from requesting user login name
            cur2.execute("select user_id from users where user_login=%s", (uname,))
            if cur2.rowcount > 1 or cur2.rowcount <= 0:
                print "More than one record or no record for a specific user login %s" % uname
                sys.exit(1)

            uid = cur2.fetchone()['user_id']

            # set up resource ownership in user_access_to_resource table
            cur2.execute("select privilege_id from privileges where privilege_code='ro'")
            if cur2.rowcount <= 0:
                print "no record for own privilege_code"
                sys.exit(1)
            privilege_id = cur2.fetchone()['privilege_id']

            cur2.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
            if cur2.rowcount <= 0:
                print "no record in resources for resource_uuid=%s" % resource_uuid
                continue
            res_id = cur2.fetchone()['resource_id']

           # only insert into user_access_to_resource when the owner privilege is not already inserted
            # this check is needed to remove a wrong previous implementation that adds all owners into edit_users and view_users tables
            cur2.execute("""select privilege_id from user_access_to_resource where user_id=%s
                        and resource_id=%s and assertion_user_id=%s""", (uid, res_id, uid))
            if cur2.rowcount <= 0:
                cur2.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                       (uid, res_id, privilege_id, uid))
                con2.commit()

except psycopg2.DatabaseError, e:
    print 'Error %s' % e
    sys.exit(1)

finally:
    if con1:
        con1.close()
    if con2:
        con2.close()

