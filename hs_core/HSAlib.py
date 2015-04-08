"""
The HSAccess library implements access control logic for scientific data sharing. It includes

1. user registration and privilege handling

2. group creation and management

3. resource registration and access control. 

"""
__author__ = 'Alva Couch'


import psycopg2
import psycopg2.extras
import uuid
# from pprint import pprint


##################################################################
# assertion logic for filesystem protection model
# This code implements a filesystem protection model.
# It is in essence a data model; the routines herein are
# get and put methods for various kinds of data.
# The key to the interface is an idempotent assertion model
# in which repeating an assertion has no effect.
# Assertions are facts about the protection of resources.
# An assertion is either made true, or an exception is raised
# indicating why it cannot be made true.
##################################################################
# to be done:
# deep logic for ownership: do not allow the last owner to disown
# - for groups (not tested)
# - for resources (not tested)
# invite/accept logic for resources
##################################################################

# exception class specifically for access control exceptions


class HSAException(Exception):
    """
    Generic Base Exception class for HSAccess class.

    *This exception is a generic base class and is never directly raised.*
    See subclasses HSAccessException, HSUsageException, and HSIntegrityException
    for details.
    """
    def __init__(self, value):
        """
        Sets the exception value to a given string. 
        """
        self.value = value

    def __str__(self):
        return repr(self.value)


class HSAccessException(HSAException):
    """
    Exception class for access control.

    This exception is raised when the access control system denies a user request.
    It can safely be caught to probe whether an operation is permitted.
    """
    def __str__(self):
        return repr("HS Access Exception: " + self.value)

    pass


class HSAUsageException(HSAException):
    """
    Exception class for parameter usage problems.

    This exception is raised when a routine is called with invalid parameters.
    This includes references to non-existent resources, groups, and users.

    This is typically a programming error and should be entered into
    issue tracker and resolved.

    *Catching this exception is not recommended.*
    """
    def __str__(self):
        return repr("HS Usage Exception: " + self.value)

    pass


class HSAIntegrityException(HSAException):
    """
    Exception class for database failures.
    This is an "anti-bugging" exception that should *never* be raised unless something
    is very seriously wrong with database configuration. This exception is only raised
    if the database fails to meet integrity constraints.

    *This cannot be a programming error.* In fact, it can only happen if the schema
    for the database itself becomes corrupt. The only way to address this is to
    repair the schema.

    *Catching this exception is not recommended.*
    """

    def __str__(self):
        return repr("HS Database Integrity Exception: " + self.value)

    pass


class HSAccessCore(object):
    """
    This class consists of the core methods that contact iRODS

    Unlike HSAccess, it does not contain helper functions;
    only the functions necessary to the core logic.
    """

    __PRIVILEGE_OWN = 1             # owner of thing
    __PRIVILEGE_RW = 2              # can read and write thing
    __PRIVILEGE_RO = 3              # can read thing
    __PRIVILEGE_NONE = 4            # code that no privilege is asserted
    __PRIVILEGE_CODES = ['own', 'rw', 'ro', 'none']

    def __init__(self, irods_user, irods_password,
                 db_database, db_user, db_password, db_host, db_port):
        try:
            self.__irods_user = irods_user
            # print 'irods_user is ', irods_user
            # could authenticate against irods here
            self.__conn = None
            self.__cur = None
            self.__conn = psycopg2.connect(database=db_database, user=db_user, password=db_password,
                                           host=db_host, port=db_port)
            self.__cur = self.__conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except:
            raise HSAIntegrityException("unable to connect to the database")
        self.__user_id = self.__get_user_id_from_login(irods_user)
        self.__user_uuid = self.get_user_uuid_from_login(irods_user)

    def __del__(self):
        if self.__conn is not None:
            self.__conn.close()

    ###########################################################
    # user handling
    ###########################################################
    # 'hs register user' for our own use.
    def assert_user(self, user_login, user_name,  user_active=True, user_admin=False, user_uuid=None):
        """
        Register or update the registration of a user

        :type user_login: str
        :type user_name: str
        :type user_active: bool
        :type user_admin: bool
        :type user_uuid: str
        :param user_login: user login name
        :param user_name: str: user print name
        :param user_active: bool: whether user is active
        :param user_admin: bool: whether user is an admin
        :param user_uuid: uuid to register or update; leave out to register a new user

        This is used in two forms:

        1. with user_uuid absent, it attempts to register a new user. Note if the specified
           login is found, that is utilized as a unique key and that record is updated instead.

        2. with user_uuid present, it updates the metadata record for that user.

        The access control model disallows certain changes to this record:

        1. Changes to whether a user is active or an administrator can only be made by an administrative user.

        2. Regular users can only change their print names (user_name).

        :todo: check logic for what a user can change.
        """
        # anti-bug main arguments
        if type(user_name) is not str:
            raise HSAUsageException("user_name is not a string")
        if type(user_login) is not str:
            raise HSAUsageException("user_login is not a string")
        if type(user_active) is not bool:
            raise HSAUsageException("user_active is not boolean")
        if type(user_admin) is not bool:
            raise HSAUsageException("user_admin is not boolean")

        if not self.user_exists(self.__user_uuid):
            raise HSAUsageException("User uuid does not exist")
        if not (self.user_is_active(self.__user_uuid)):
            raise HSAccessException("User is inactive")
        if not (self.user_is_admin(self.__user_uuid)):
            raise HSAccessException("User is not an administrator")

        if user_uuid is None:
            # try the other keys to see if it is defined
            try:
                user_uuid = self.get_user_uuid_from_login(user_login)
            except HSAException:
                user_uuid = uuid.uuid4().hex
        # print "resource uuid is", resource_uuid

        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")

        assert_id = self.__get_user_id_from_uuid(self.__user_uuid)

        if self.user_exists(user_uuid):
            self.__assert_user_update(assert_id, user_uuid, user_login, user_name, user_active, user_admin)
        else:
            self.__assert_user_add(assert_id, user_uuid, user_login, user_name, user_active, user_admin)

        return user_uuid

    def __assert_user_add(self, assertion_user_id, user_uuid, user_login, user_name,
                          user_active=True, user_admin=False):
        """
        PRIVATE: add a new user record

        :type assertion_user_id: int
        :type user_uuid: str
        :type user_login: str
        :type user_name: str
        :type user_active: bool
        :type user_admin: bool
        :param assertion_user_id: internal user id of user adding the login name
        :param user_uuid: uuid of user to add
        :param user_login: user login string: must be unique
        :param user_name: user print name
        :param user_active: whether user is active
        :param user_admin: whether user is an administrator

        Add a new previously non-existent user record to the registered users. user_uuid and user_login
        must both be independently unique.

        This routine is not subject to access control restrictions.
        """
        self.__cur.execute("""insert into users values (DEFAULT, %s, %s, %s, %s, %s, %s, DEFAULT)""",
                           (user_uuid, user_login, user_name, user_active, user_admin, assertion_user_id))
        self.__conn.commit()

    # this is the general idea but can be cleaned up with conditional code.
    def __assert_user_update(self, assertion_user_id, user_uuid, user_login, user_name,
                             user_active=True, user_admin=False):
        """
        PRIVATE: update an existing user record

        :type user_login: str
        :type assertion_user_id: int
        :type user_uuid: str
        :type user_name: str
        :type user_active: bool
        :type user_admin: bool
        :param user_login: login of user to update (primary key)
        :param assertion_user_id: user adding the login name
        :param user_uuid: user uuid string: must be unique
        :param user_name: user print name
        :param user_active: whether user is active
        :param user_admin: whether user is an administrator

        Update an existing user record in the registered users table. user_uuid and user_login must
        remain independently unique.

        This routine is not subject to access control restrictions.
        """
        self.__cur.execute("""update users set user_login =%s, user_name=%s, user_active=%s, user_admin=%s,
                              assertion_user_id=%s, assertion_time=CURRENT_TIMESTAMP
                              where user_uuid=%s""",
                           (user_login, user_name, user_active, user_admin, assertion_user_id, user_uuid))
        self.__conn.commit()

    ###########################################################
    # user state
    ###########################################################
    # test whether a login exists without recovering its id or metadata
    def user_exists(self, user_uuid=None):
        """
        Determine whether a login name is registered in the HSAccess database

        :type user_uuid: str
        :param user_uuid: uuid of user; omit to report on current user
        :return: True if user exists
        :rtype: bool

        This checks a uuid and returns True if it exists. This is used to avoid
        unintentional exceptions from use of a non-existent uuid.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        try:
            self.get_user_metadata(user_uuid)
            return True
        except HSAUsageException:
            return False

    # test whether a user login has administrative privileges
    def user_is_admin(self, user_uuid=None):
        """
        Determine whether a user identified by uuid has admin privileges

        :type user_uuid: str
        :param user_uuid: uuid of user; omit to report on current user
        :return: True if user has admin privileges 
        :rtype: bool

        This reports whether the given user has administrative privileges.
        Administrative users can, for example:

        1. register new users with 'assert_user'

        2. impersonate a given user and perform selected operations by proxy for the user.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        meta = self.get_user_metadata(user_uuid)
        return meta['admin']

    # test whether a user login is entitled to make changes
    def user_is_active(self, user_uuid=None):
        """
        Determine whether a user uuid is an active user

        :type user_uuid: str
        :param user_uuid: uuid of user; omit to report on current user
        :return: True if user is active.
        :rtype: bool

        This reports whether a given user is active. Inactive users cannot login or access anything,
        but their privileges and owned documents are kept intact. It is legal for a resource or group
        to be owned by an inactive user, and groups and resources originally created by an inactive user
        continue to be available to others. Whether a group is active is independent of whether its
        owner is active.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        meta = self.get_user_metadata(user_uuid)
        return meta['active']

    ###########################################################
    # user system metadata
    ###########################################################

    # get a specific login id for use as an entity id for recording actions
    def __get_user_id_from_login(self, login):
        """
        PRIVATE: get user database id from login name

        :type login: str
        :param login: string login name
        :return: integer user id
        :rtype: int
        """
        self.__cur.execute("select user_id from users where user_login=%s", (login,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific user login")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['user_id']
        else:
            raise HSAUsageException("User login does not exist")

    # get a specific login id for use as an entity id for recording actions
    def __get_user_id_from_uuid(self, user_uuid=None):
        """
        PRIVATE: get user database id from user uuid

        :type user_uuid: str
        :param user_uuid: uuid of user; omit to report on current user
        :return: user id for use in internal functions. 
        :rtype: int

        The return value of this function is used as the internal key in the
        access control database, but never, ever exposed to users. It is
        an integer for speed of joins.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("select user_id from users where user_uuid=%s", (user_uuid,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific user uuid")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['user_id']
        else:
            raise HSAUsageException("User uuid does not exist")

    # get a specific login for use as a logging aid
    def __get_user_login_from_uuid(self, user_uuid=None):
        """
        PRIVATE: get user login name from user uuid e

        :type user_uuid: str
        :param user_uuid: uuid of user; omit to report on current user
        :return: user login name. 
        :rtype: str

        This returns the login name for a given user uuid. This is currently an iRODS login and has no
        meaning in the system. It is used as a last resort in 'assert_user' to insure that we do not
        create users with identical login names, but is otherwise ignored.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("select user_login from users where user_uuid=%s", (user_uuid,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific user uuid")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['user_login']
        else:
            raise HSAUsageException("User uuid does not exist")

    # get a specific login uuid for use in requesting actions
    def get_user_uuid_from_login(self, login):
        """
        PRIVATE: get user database id from login name

        :type login: str
        :param login: string login name
        :return: user uuid
        :rtype: str

        This returns the user uuid from the login name. While this works reliably
        because login names are unique, this is only used to construct test cases.
        """
        if type(login) is not str:
            raise HSAUsageException("login is not a string")

        self.__cur.execute("select user_uuid from users where user_login=%s", (login,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific user login")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['user_uuid']
        else:
            raise HSAUsageException("User login does not exist")

    # fetch a list of all user logins
    def __get_user_logins(self):
        """
        PRIVATE: Get a list of all registered user logins

        :return: list of login names
        :rtype: List<str>

        Gets a list of user login names. These are used internally as unique
        identifiers but not accepted as command parameters.
        """
        self.__cur.execute("SELECT user_login FROM users order by user_login")
        result = []
        rows = self.__cur.fetchall()
        for row in rows:
            result += [row['user_login']]
        return result

    ###########################################################
    # fetch a list of all user metadata
    # CLI: hs_users
    ###########################################################

    def get_users(self):
        """
        Get the registered user list

        :return: list of user metadata dictionaries
        :rtype: list[dict[str, str]]

        Return format is a list of dictionaries of the form::

            {
            'login': *user_login*,
            'uuid': *user uuid*,
            'name': *user name*,
            'active': *true if user is active*,
            'admin':  *true if user is admin*
            }

        These entries can be edited and used as input to 'assert_user_metadata'.
        """
        self.__cur.execute("SELECT user_uuid, user_login, user_name, user_active, user_admin FROM users")
        result = []
        rows = self.__cur.fetchall()
        for row in rows:
            result += [
                {
                    'login': row['user_login'],
                    'uuid': row['user_uuid'],
                    'name': row['user_name'],
                    'active': row['user_active'],
                    'admin': row['user_admin']
                }
            ]
        return result

    def get_user_metadata(self, user_uuid=None):
        """
        Get metadata for a user as a dict record

        :type user_uuid: str
        :param user_uuid: uuid of user for which to fetch metadata; If None, then return data on current user.
        :return: Dict of metadata for the login specified
        :rtype: Dict

        This gives more complete information than 'get_users', including the date of user creation.
        The extra data is not utilize in 'assert_user_metadata'.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("""select u.user_login, u.user_uuid, u.user_name, u.user_active, u.user_admin,
          a.user_login as user_assertion_login, a.user_uuid as user_assertion_uuid, u.assertion_time
          from users u left join users a on u.assertion_user_id = a.user_id
          where u.user_uuid=%s""", (user_uuid,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific user login")
        if self.__cur.rowcount > 0:
            row = self.__cur.fetchone()
            return {'uuid':  row['user_uuid'],
                    'login': row['user_login'],
                    'name': row['user_name'],
                    'active': row['user_active'],
                    'admin': row['user_admin'],
                    'asserting_login': row['user_assertion_login'],
                    'asserting_uuid': row['user_assertion_uuid'],
                    'assertion_time': row['assertion_time']}
        else:
            raise HSAUsageException('User uuid does not exist')

    def assert_user_metadata(self, metadata):
        """
        Assert changes in user metadata

        :type metadata: dict<str, str>
        :param metadata: a metadata record returned by get_user_metadata

        Permissible assertions are those permissible to the currently logged-in user.
        """
        user_uuid = metadata['uuid']
        if not self.user_exists(user_uuid):
            raise HSAUsageException("User uuid does not exist")
        if user_uuid != self.get_uuid() and not self.user_is_admin(self.get_uuid()):
            raise HSAccessException("Regular user cannot assert metadata for users other than self")
        if metadata['admin'] and not self.user_is_admin():
            raise HSAccessException("Regular user cannot make self an administrator")
        if not metadata['active'] and not self.user_is_admin():
            raise HSAccessException("Regular user cannot deactivate a user")
        self.assert_user(metadata['login'], metadata['name'],
                         metadata['active'], metadata['admin'], metadata['uuid'])

    ###########################################################
    # user group handling
    ###########################################################

    # fetch a list of all group uuids
    def get_groups(self):
        """
        Get information on all existing groups

        :return: a list of all group uuids and names, as dictionary objects
        :rtype: Dict 

        This returns a list of elements of the form::

            { 'uuid': *uuid of group*, 'name': *name of group* }

        sorted in order of group name. Group names do not have to be unique.

        The 'uuid' element can be used as input to 'get_group_metadata' to learn more about the group.

        Note: this method is not currently subject to access control. The access control document does
        not limit group visibility; just membership.
        """
        self.__cur.execute("SELECT group_uuid, group_name FROM groups ORDER BY group_name, group_uuid")
        result = []
        rows = self.__cur.fetchall()
        for row in rows:
            result += [{'uuid': row['group_uuid'], 'name': row['group_name']}]
        return result

    def get_groups_for_user(self, user_uuid=None):
        """
        Get a list of groups relevant to a specific user

        :param user_uuid: the user to report on; omit to report on current user.
        :return: list of dicts describing groups
        :rtype: list[dict[str, str]] 

        This returns a list of groups in the following format::
            { 'name': *name of group*, 'uuid': *uuid of group* } ]
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("""select g.group_uuid, g.group_name, x.privilege_code
                          from groups g
                          left join user_membership_in_group m on m.group_id=g.group_id
                          left join users u on u.user_id = m.user_id
                          left join user_group_privilege p on p.user_id=u.user_id and p.group_id=g.group_id
                          left join privileges x on x.privilege_id=p.privilege_id
                          where u.user_uuid=%s
                          order by g.group_name, g.group_uuid""",
                           (user_uuid,))
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'uuid': row['group_uuid'], 'name': row['group_name'], 'code': row['privilege_code']}]
        return result

    def get_public_groups(self):
        """
        Get a list of groups relevant to a specific user

        :return: list of dicts describing groups
        :rtype: list[dict[str, str]]

        This returns a list of groups in the following format::
            { 'name': *name of group*, 'uuid': *uuid of group* } ]
        """
        self.__cur.execute("""select g.group_uuid, g.group_name, 'ro' AS privilege_code
                           from groups g
                           where g.group_public=TRUE
                           order by g.group_name, g.group_uuid""", ())
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'uuid': row['group_uuid'], 'name': row['group_name'], 'code': row['privilege_code']}]
        return result

    def get_discoverable_groups(self):
        """
        Get a list of groups that are discoverable

        :return: list of dicts describing groups
        :rtype: list[dict[str, str]]

        This returns a list of groups in the following format::
            { 'name': *name of group*, 'uuid': *uuid of group* } ]
        """
        self.__cur.execute("""select g.group_uuid, g.group_name,
                           CASE WHEN g.group_public THEN 'ro'
                                ELSE 'none'
                           END AS privilege_code
                           from groups g
                           where g.group_discoverable = TRUE
                           order by g.group_name, g.group_uuid""")
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'uuid': row['group_uuid'], 'name': row['group_name'], 'code': row['privilege_code']}]
        return result

    def get_group_members(self, group_uuid):
        """
        Get a list of members of a specific group

        :param group_uuid: the group to report on; omit to report on current user.
        :return: list of dicts describing groups
        :rtype: list[dict[str, str]] 

        This returns a list of groups in the following format::
            { 'name': *name of group*, 'uuid': *uuid of group* } ]
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        # THIS SHOULD HONOR group_public flags and user flags
        if not self.group_is_public(group_uuid) and not self.group_is_owned(group_uuid):
            raise HSAccessException("User must be owner or administrator")
        self.__cur.execute("""select u.user_uuid, u.user_name, x.privilege_code
                              from groups g
                              left join user_group_privilege p on p.group_id=g.group_id
                              left join users u on u.user_id = p.user_id
                              left join privileges x on x.privilege_id=p.privilege_id
                              where g.group_uuid=%s
                              order by u.user_name, u.user_uuid""",
                           (group_uuid,))
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'uuid': row['user_uuid'], 'name': row['user_name'], 'code': row['privilege_code']}]
        return result

    def get_group_metadata(self, group_uuid):
        """
        Get metadata for a group as a dict record

        :param group_uuid: uuid of group
        :return: dict of group metadata
        :rtype: Dict 

        This returns a dictionary record with the structure::

            {
                'uuid': *uuid of group*,
                'name': *name of group*,
                'active': *whether group is active*,
                'discoverable': *whether group existence is discoverable*,
                'public': *whether group members are published*,
                'asserting_login': *login of user who last changed metadata*,
                'asserting_uuid': *uuid of user who last changed metadata*,
                'assertion_time': *time of last metadata change*
            }

        This value can be edited and used as an argument to 'assert_group_metadata'.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        self.__cur.execute("""select g.group_uuid, g.group_name,
          g.group_active, g.group_shareable, g.group_discoverable, g.group_public,
          a.user_login as user_assertion_login, a.user_uuid as user_assertion_uuid, g.assertion_time
          from groups g left join users a on g.assertion_user_id = a.user_id
          where g.group_uuid=%s""", (group_uuid,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific group uuid")
        if self.__cur.rowcount > 0:
            row = self.__cur.fetchone()
            return {'uuid': row['group_uuid'],
                    'name': row['group_name'],
                    'active': row['group_active'],
                    'shareable': row['group_shareable'],
                    'discoverable': row['group_discoverable'],
                    'public': row['group_public'],
                    'asserting_login': row['user_assertion_login'],
                    'asserting_uuid': row['user_assertion_uuid'],
                    'assertion_time': row['assertion_time']}
        else:
            raise HSAUsageException("Group uuid does not exist")

    def assert_group_metadata(self, metadata):
        """
        Assert changes in user metadata

        :param metadata: a metadata record as returned by get_group_metadata

        This asserts changes in group metadata subject to the restrictions in 'assert_group'.
        It can be used to create new groups as well as to edit group metadata.
        """
        user_uuid = self.get_uuid()
        self.assert_group(metadata['name'],
                          metadata['active'], metadata['shareable'], metadata['discoverable'], metadata['public'],
                          group_uuid=metadata['uuid'], user_uuid=user_uuid)

    ###########################################################
    # group system metadata
    ###########################################################

    # get a specific login id for use as an entity id for recording actions
    def __get_group_id_from_uuid(self, group_uuid):
        """
        PRIVATE: translate from group object identifier to database id

        :type group_uuid: str
        :param group_uuid: group object identifier
        :return: group_id in HSAccess database, for use in internal functions. 
        :rtype: int 

        This returns the private identifier for a group that is used internally as
        a join target. This is an integer for speed. This identifier is never exposed
        to users or administrators of the system.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        self.__cur.execute("select group_id from groups where group_uuid=%s", (group_uuid,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific group uuid")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['group_id']
        else:
            raise HSAUsageException("Group uuid does not exist")

    # get a specific login id for use as an entity id for recording actions
    def __get_group_name_from_uuid(self, group_uuid):
        """
        PRIVATE: translate from group object identifier to database id

        :type group_uuid: str
        :param group_uuid: group object identifier
        :return: group name
        :rtype: str 

        This returns the name of a group from its uuid. Group names are not generally unique and
        cannot be used as keys from which to locate groups.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        meta = self.get_group_metadata(group_uuid)
        return meta['name']

    # this is a no-frills assert user without object use
    # CLI: hs create group and hs modify group
    def assert_group(self, group_name,
                     group_active=True, group_shareable=True, group_discoverable=True, group_public=True,
                     group_uuid=None, user_uuid=None):
        """
        Register or update a group

        :type group_name: str
        :type group_active: bool
        :type group_shareable: bool
        :type group_discoverable: bool
        :type group_public: bool
        :type group_uuid: str
        :type user_uuid: str
        :param group_name: str: name of group
        :param group_active: bool: whether group is active
        :param group_shareable: bool: whether group can be managed by non-owners.
        :param group_discoverable: bool: whether group and owners are discoverable in listings.
        :param group_public: bool: whether group members are publicly accessible.
        :param group_uuid: str: group identifier, if omitted or unset, then a new group_uuid is created and returned.
        :param user_uuid: user identifier; omit to utilize current user.
        :return: uuid of group just modified; created if necessary.
        :rtype: str 

        This creates a new group subject to several conventions:

        1. if group_uuid is None, then a new group uuid is created.

        2. if user_uuid is not None and the current user has admin privilege,
           then the operation is undertaken on behalf of the stated user.

        This is also subject to access control limits:

        1. Any regular user can create a group

        2. After the group is created, a regular user can only change its name.

        3. All other changes to a group require administrative privilege.

        4. The group_uuid is set forever and cannot change.

        :todo: ensure that regular users cannot change too much!
        """
        # anti-bug main arguments
        if type(group_name) is not str:
            raise HSAUsageException("group_name is not a string")
        if type(group_active) is not bool:
            raise HSAUsageException("group_active is not boolean")
        if type(group_shareable) is not bool:
            raise HSAUsageException("group_shareable is not boolean")
        if type(group_discoverable) is not bool:
            raise HSAUsageException("group_discoverable is not boolean")
        if type(group_public) is not bool:
            raise HSAUsageException("group_public is not boolean")

        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (self.user_exists(user_uuid)):
            raise HSAUsageException("User uuid does not exist")

        # check for admin privilege or user match
        if user_uuid != self.get_uuid() and not (self.user_is_admin()):
            raise HSAccessException("User is not an administrator")

        if group_uuid is None:
            group_uuid = uuid.uuid4().hex

        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")

        assert_id = self.__get_user_id_from_uuid(user_uuid)
        if self.group_exists(group_uuid):
            if self.user_is_admin(self.get_uuid()) or self.group_is_owned(group_uuid):
                self.__assert_group_update(assert_id, group_uuid, group_name,
                                           group_active, group_shareable,
                                           group_discoverable, group_public)
            else:
                raise HSAccessException("Regular user must own group")
        else:
            # NEW GROUP:
            # 1) add new group to group list
            self.__assert_group_add(assert_id, group_uuid, group_name,
                                    group_active, group_shareable, group_discoverable, group_public)

            # 2) make the asserting user the owner
            # it is necessary to run around protections for this one step
            # because of a chicken-and-egg problem
            privilege_id = self.__get_privilege_id_from_code('own')
            group_id = self.__get_group_id_from_uuid(group_uuid)
            self.__share_group_user_add(assert_id, assert_id, group_id, privilege_id)

        return group_uuid

    def __assert_group_add(self, assertion_user_id, group_uuid, group_name,
                           group_active, group_shareable, group_discoverable, group_public):
        """
        PRIVATE: add a new group to the registry

        :type assertion_user_id: int
        :type group_uuid: str
        :type group_name: str
        :type group_active: bool
        :type group_shareable: bool
        :type group_discoverable: bool
        :type group_public: bool
        :param assertion_user_id: internal id of requesting user
        :param group_uuid: group identifier
        :param group_name: name of group
        :param group_active: whether group is active.
        :param group_shareable: whether group can be managed by non-owners.
        :param group_discoverable: whether group is discoverable in listings.
        :param group_public: whether group members are listable.

        Notes:

        1. This is not subject to access control.

        2. An exception is raised if the group uuid already exists.

        """
        self.__cur.execute("""insert into groups values (DEFAULT, %s, %s, %s, %s, %s, %s, %s, DEFAULT)""",
                           (group_uuid, group_name, group_active,
                            group_shareable, group_discoverable, group_public, assertion_user_id))
        self.__conn.commit()

    def __assert_group_update(self, assertion_user_id, group_uuid, group_name,
                              group_active, group_shareable, group_discoverable, group_public):
        """
        PRIVATE: update a group record in the registry

        :type assertion_user_id: int
        :type group_uuid: str
        :type group_name: str
        :type group_active: bool
        :param assertion_user_id: internal id of requesting user
        :param group_uuid: group identifier
        :param group_name: name of group
        :param group_active: group active or retired

        Notes:

        1. This is not subject to access control.

        2. An exception is raised if the group uuid does not exist.


        """
        self.__cur.execute("""update groups set group_name=%s,
                              group_active=%s,
                              group_shareable=%s,
                              group_discoverable=%s,
                              group_public=%s,
                              assertion_user_id=%s,
                              assertion_time=CURRENT_TIMESTAMP
                              where group_uuid=%s""",
                           (group_name, group_active, group_shareable,
                            group_discoverable, group_public,
                            assertion_user_id, group_uuid))
        self.__conn.commit()

    # CLI: hs_delete_group
    # unsure whether this should be a possibility;
    # consider deactivate_group instead.
    def retract_group(self, group_uuid):
        """
        Delete a group and all membership information

        :type group_uuid: str
        :param group_uuid: uuid of group to delete

        Retractions are handled via database cascade logic. This deletes all information about the
        group, including every resource held with that group.

        *Consider making a group inactive instead of using this routine.*

        Restrictions:

        1. Only the owner of the group or an administrator can do this.

        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        # only an owner or administrator can retract a group
        if not self.user_is_admin(self.get_uuid()) \
                and not self.group_is_owned(group_uuid, self.get_uuid()):
            raise HSAccessException("Regular user must own group")
        group_id = self.__get_group_id_from_uuid(group_uuid)
        self.__cur.execute("""delete from user_access_to_group where group_id=%s""", (group_id,))
        # user_membership_in_group is now a view
        # self.__cur.execute("""delete from user_membership_in_group where group_id=%s""", (group_id,))
        self.__cur.execute("""delete from groups where group_id=%s""", (group_id,))
        self.__conn.commit()

    ###########################################################
    # group state
    ###########################################################
    # test whether a group exists without retrieving its metadata
    def group_exists(self, group_uuid):
        """
        Determine whether group identifier (uuid) is registered

        :type group_uuid: str
        :param group_uuid: group object identifier
        :return: whether group object identifier is registered
        :rtype: bool 

        This is used to avoid execution exceptions by ensuring that a group uuid
        is valid before performing further actions.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        try:
            self.get_group_metadata(group_uuid)
            return True
        except HSAUsageException:
            return False

    def group_is_active(self, group_uuid):
        """
        True if a group is active

        :type group_uuid: str
        :param group_uuid: group identifier
        :return: True if group is active.
        :rtype: bool 
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        meta = self.get_group_metadata(group_uuid)
        return meta['active']

    def group_is_shareable(self, group_uuid):
        """
        True if a group is shareable

        :type group_uuid: str
        :param group_uuid: group identifier
        :return: True if group is shareable.
        :rtype: bool 

        If a group is shareable, then users with readwrite privilege can invite members. Otherwise, they cannot.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        meta = self.get_group_metadata(group_uuid)
        return meta['shareable']

    def group_is_discoverable(self, group_uuid):
        """
        True if a group is discoverable

        :type group_uuid: str
        :param group_uuid: group identifier
        :return: True if group is discoverable.
        :rtype: bool 

        If a group is discoverable, then it appears in the active groups along with its owner contact information.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        meta = self.get_group_metadata(group_uuid)
        return meta['discoverable']

    def group_is_public(self, group_uuid):
        """
        True if a group is public

        :type group_uuid: str
        :param group_uuid: group identifier
        :return: True if group is discoverable.
        :rtype: bool 

        If a group is public, then others can see group members.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        meta = self.get_group_metadata(group_uuid)
        return meta['public']

    ###########################################################
    # resource handling
    ###########################################################

    def __get_resource_id_from_uuid(self, resource_uuid):
        """
        PRIVATE: get resource_id from resource digital identifier (uuid)

        :type resource_uuid: str
        :param resource_uuid:  resource object identifier
        :return: private resource_id in HSAccess database, for use in internal functions. 
        :rtype: int 

        This returns the private and internal unique identifier of the resource object.
        This id is never exposed to users.

        Note: this method is not subject to access control.
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")
        self.__cur.execute("select resource_id from resources where resource_uuid=%s", (resource_uuid,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific resource uuid")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['resource_id']
        else:
            raise HSAUsageException("Resource uuid does not exist")

    def __get_resource_uuid_from_path(self, resource_path):
        """
        PRIVATE: get resource_uuid from (unique) resource path

        :type resource_path: str
        :param resource_path: str: resource object path in iRODS
        :return: resource_uuid in HSAccess database, for use in internal functions. 
        :rtype: int 

        Paths in iRODS are assumed to be unique. This does the same thing as '__get_resource_id_from_uuid'
        but for paths rather than uuids.

        Note: this method is not subject to access control.
        """
        self.__cur.execute("select resource_uuid from resources where resource_path=%s", (resource_path,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific resource path")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['resource_uuid']
        else:
            raise HSAUsageException("Resource path does not exist")

    def get_resource_metadata(self, resource_uuid):
        """
        Get metadata for a resource as a dict record

        :type resource_uuid: str
        :param resource_uuid: resource identifier for which to fetch metadata
        :return: Dict object containing all metadata for a resource. 
        :rtype: Dict

        This returns a dictionary item of the format::

            {
            'title': *title of resource*,
            'uuid': *uuid of resource*,
            'path': *path of resource*,
            'shareable': *whether resource is shareable*,
            'discoverable': *whether resource is discoverable*,
            'public': *whether resource is publicly accessible*,
            'published': *whether resource is published and has a DOI*,
            'immutable': *whether resource is immutable*,
            'asserting_login': *login of user who made last change to metadata*,
            'asserting_uuid': *uuid of user who made last change to metadata*,
            'assertion_time': *time of last change to metadata*
            }

        The record returned from 'get_resource_metadata' is suitable for use in
        'assert_resource_metadata' and may be used for things like cloning resources.

        The 'asserting_uuid' is not used during 'assert_resource_metadata'; this is a record
        of "who to blame" for the last change.

        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        self.__cur.execute("""select r.resource_uuid, r.resource_path,
          r.resource_title, r.resource_immutable, r.resource_published,
          r.resource_discoverable, r.resource_public,
          r.resource_shareable,
          a.user_login as user_assertion_login,
          a.user_uuid as user_assertion_uuid,
          r.assertion_time
          from resources r left join users a on r.assertion_user_id = a.user_id
          where r.resource_uuid=%s""", (resource_uuid,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("Database integrity violation: "
                                        + "more than one record for a specific resource uuid")
        if self.__cur.rowcount > 0:
            row = self.__cur.fetchone()
            return {'title': row['resource_title'],
                    'uuid':  row['resource_uuid'],
                    'path': row['resource_path'],
                    'discoverable': row['resource_discoverable'],
                    'public': row['resource_public'],
                    'immutable': row['resource_immutable'],
                    'published': row['resource_published'],
                    'shareable': row['resource_shareable'],
                    'asserting_login': row['user_assertion_login'],
                    'asserting_uuid': row['user_assertion_uuid'],
                    'assertion_time': row['assertion_time']}
        else:
            raise HSAUsageException("Resource uuid does not exist")

    def assert_resource_metadata(self, metadata, user_uuid=None):
        """
        Assert changes in resource metadata

        :type metadata: dict
        :param metadata: a metadata record as returned by get_resource_metadata

        This is a wrapper for 'assert_resource' that connects it to a return value
        format from 'get_resource_metadata'. This can be used to edit resource
        fields incrementally.
        """
        self.assert_resource(metadata['path'], metadata['title'], metadata['uuid'], user_uuid,
                             metadata['immutable'], metadata['published'],
                             metadata['discoverable'], metadata['public'],
                             metadata['shareable'])

    # a primitive resource instantiation without objects
    # CLI: currently this can only be done properly through django
    # but we need a debugging command "hs register path" for our own use

    def assert_resource(self, resource_path, resource_title,
                        resource_uuid=None, user_uuid=None,
                        resource_immutable=False, resource_published=False,
                        resource_discoverable=False, resource_public=False,
                        resource_shareable=True):
        """
        Add or modify a resource in the resource registry

        :type resource_path: str
        :type resource_title: str
        :type resource_shareable: bool
        :type resource_immutable: bool
        :type resource_published: bool
        :type resource_discoverable: bool
        :type resource_public: bool
        :type resource_shareable: bool
        :type resource_uuid: str
        :type user_uuid: str
        :param resource_path: path to resource in iRODS  title
        :param resource_title: human-readable title
        :param resource_immutable: whether resource is immutable
        :param resource_published: whether resource is published
        :param resource_discoverable: whether the existence of the resource should be advertised to others
        :param resource_public: whether the data of the resource should be available to everyone
        :param resource_shareable: whether resource is shareable by non-owners
        :param resource_uuid: resource identifier
        :param user_uuid: user identifier of asserting user; omit to use current user.
        :return: resource identifier used
        :rtype: str

        This routine creates or changes resource parameters.

        This is subject to several access control rules:

        1. If resource_uuid is not None, it takes this parameter as the uuid of the resource.

        2. If resource_uuid is None, it first tries to locate the path in the resources table.
           Notwithstanding that, it creates a new resource uuid.

        Then it creates or updates a record and returns the resource uuid

        Regular users can:

        1. Create a new resource.

        2. Edit the title only of an existing resource.

        Administrative users can:

        1. Act as proxy for other users.

        2. Edit any part of the resource registration.

        If user_uuid is not None, then the operation is done on behalf of the stated user
        as an administrator. If admin privileges are not present in this case,
        an exception is raised.
        """
        # anti-bug usage by requireing argument types
        if type(resource_title) is not unicode:
            raise HSAUsageException("resource_title is not a unicode or str")
        if not(type(resource_path) is unicode or type(resource_path) is str):
            raise HSAUsageException("resource_path is not a string or unicode")
        if type(resource_shareable) is not bool:
            raise HSAUsageException("resource_shareable is not boolean")
        if type(resource_discoverable) is not bool:
            raise HSAUsageException("resource_discoverable is not boolean")
        if type(resource_public) is not bool:
            raise HSAUsageException("resource_public is not boolean")
        if type(resource_published) is not bool:
            raise HSAUsageException("resource_published is not boolean")
        if type(resource_immutable) is not bool:
            raise HSAUsageException("resource_immutable is not boolean")

        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (self.user_exists(user_uuid)):
            raise HSAUsageException("User uuid does not exist")
        requesting_user_id = self.__get_user_id_from_uuid(user_uuid)

        # check for admin privilege or user match
        if user_uuid != self.get_uuid() and not (self.user_is_admin()):
            raise HSAccessException("User is not an administrator")

        # this feature is controversial
        if resource_uuid is None:
            # try the other keys to see if it is defined
            try:
                resource_uuid = self.__get_resource_uuid_from_path(resource_path)
            except HSAException:
                resource_uuid = uuid.uuid4().hex

        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        # print "resource uuid is", resource_uuid
        if self.resource_exists(resource_uuid):
            meta = self.get_resource_metadata(resource_uuid)
            # check each privileged flag for differences
            if resource_immutable is not meta['immutable'] \
                    or resource_public is not meta['public'] \
                    or resource_published is not meta['published'] \
                    or resource_discoverable is not meta['discoverable'] \
                    or resource_shareable is not meta['shareable']:
                if not self.resource_is_owned(resource_uuid, user_uuid):
                    raise HSAccessException("Regular user must own resource")
            # changing the path requires admin
            if resource_path != meta['path']:
                if not self.user_is_admin():
                    raise HSAccessException("User must be an administrator")
            # making mutable again requires admin
            if not resource_immutable and resource_immutable != meta['immutable'] and not self.user_is_admin():
                raise HSAccessException("Resource is marked as immutable")
            # only admin users or owners can change the resource title and flags
            if self.user_is_admin(self.get_uuid()) or self.resource_is_owned(resource_uuid):
                self.__assert_resource_update(requesting_user_id, resource_uuid,
                                              resource_path, resource_title,
                                              resource_immutable, resource_published,
                                              resource_discoverable, resource_public,
                                              resource_shareable)
            else:
                raise HSAccessException("Regular user must own resource")
        else:
            # NEW RESOURCE
            # 1) put the resource into the registry
            self.__assert_resource_add(requesting_user_id, resource_uuid,
                                       resource_path, resource_title,
                                       resource_immutable, resource_published,
                                       resource_discoverable, resource_public,
                                       resource_shareable)
            # 2) make it owned by the asserting user
            # get the newly minted resource id
            resource_id = self.__get_resource_id_from_uuid(resource_uuid)
            privilege_id = self.__get_privilege_id_from_code('own')
            # This bypasses checks because this user created the resource.
            self.__share_resource_user_add(requesting_user_id, requesting_user_id, resource_id, privilege_id)
            # add owner logic here
        return resource_uuid

    # subfunction: add a resource whose uuid (primary key) does not exist
    # this has no inherent protection and is used internally for some
    # initial creation tasks.
    def __assert_resource_add(self, requesting_user_id, resource_uuid,
                              resource_path, resource_title,
                              resource_immutable, resource_published,
                              resource_discoverable, resource_public,
                              resource_shareable):
        """
        PRIVATE: add a new resource to the registry. 

        :type resource_path: str
        :type resource_title: str
        :type resource_shareable: bool
        :type resource_immutable: bool
        :type resource_published: bool
        :type resource_discoverable: bool
        :type resource_public: bool
        :type resource_shareable: bool
        :type resource_uuid: str
        :param requesting_user_id: user id of adding person
        :param resource_uuid: resource identifier
        :param resource_path: path in iRODS
        :param resource_title: human-readable title
        :param resource_immutable: whether resource is immutable to change
        :param resource_published: whether resource is published
        :param resource_discoverable: whether the existence of the resource should be advertised to others
        :param resource_public: whether the data of the resource should be available to everyone
        :param resource_shareable: whether resource is shareable by non-owners

        This adds a new and previously non-existent resource to the resource registry. resource_uuid and
        resource_path must be unique. If these are not unique, an exception is raised.

        Note: this routine is not subject to access control restrictions.
        """
        self.__cur.execute("""insert into resources values (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, DEFAULT)""",
                           (resource_uuid, resource_path, resource_title,
                            resource_immutable, resource_published,
                            resource_discoverable, resource_public,
                            resource_shareable, requesting_user_id))
        self.__conn.commit()

    # subfunction: update a resource whose uuid is known
    def __assert_resource_update(self, requesting_user_id, resource_uuid,
                                 resource_path, resource_title,
                                 resource_immutable, resource_published,
                                 resource_discoverable, resource_public,
                                 resource_shareable):
        """
        PRIVATE: add a new resource to the registry

        :type requesting_user_id: int
        :type resource_uuid: str
        :type resource_path: str
        :type resource_title: str
        :type resource_immutable: bool
        :type resource_published: bool
        :type resource_discoverable: bool
        :type resource_public: bool
        :type resource_shareable: bool
        :type resource_discoverable: bool
        :type resource_public: bool
        :type resource_shareable: bool
        :param requesting_user_id: user id of adding person
        :param resource_uuid: resource identifier
        :param resource_path: path in iRODS
        :param resource_title: human-readable title
        :param resource_immutable: whether resource is immutable
        :param resource_published: whether resource is published
        :param resource_discoverable: whether the existence of the resource should be advertised to others
        :param resource_public: whether the data of the resource should be available to everyone
        :param resource_shareable: whether resource is shareable by non-owners

        This updates an existing resource to the resource registry. resource_uuid and
        resource_path must be unique and a record for resource_uuid must be present.
        If these requirements are not met, an exception is raised.

        Note: this routine is not subject to access control restrictions.
        """
        self.__cur.execute("""update resources set resource_path=%s, resource_title=%s,
                              resource_immutable=%s, resource_published=%s,
                              resource_discoverable=%s, resource_public=%s,
                              resource_shareable=%s,
                              assertion_user_id=%s, assertion_time=CURRENT_TIMESTAMP
                              where resource_uuid=%s""",
                           (resource_path, resource_title,
                            resource_immutable, resource_published,
                            resource_discoverable, resource_public,
                            resource_shareable,
                            requesting_user_id, resource_uuid))
        self.__conn.commit()

    # CLI: hs delete resource
    # unsure whether this should be a possibility;
    # consider deactivate_group instead.

    def retract_resource(self, resource_uuid):
        """
        Delete a resource and all privilege information

        :type resource_uuid: str
        :param resource_uuid: uuid of resource to delete

        Retractions are handled via database cascade logic (ON DELETE CASCADE).
        This deletes all information about the resource, including all privilege
        over it.

        Restrictions:

        1. Only the owner of the group or an administrator can do this.

        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        # only an owner or administrator can retract a group
        if not self.user_is_admin(self.get_uuid()) \
                and not self.resource_is_owned(resource_uuid, self.get_uuid()):
            raise HSAccessException("Regular user must own resource")
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        # no longer needed: cascade logic enables this
        # self.__cur.execute("""delete from user_access_to_resource where group_id=%s""", (group_id,))

        self.__cur.execute("""delete from resources where resource_id=%s""", (resource_id,))
        self.__conn.commit()

    ###########################################################
    # resource state
    ###########################################################
    def resource_exists(self, resource_uuid):
        """
        Determine whether a resource is registered in the database

        :type resource_uuid: str
        :param resource_uuid: resource identifier
        :return: whether resource is registered
        :rtype: bool 

        This determines whether a given resource uuid corresponds to an existing resource.
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        try:
            self.get_resource_metadata(resource_uuid)
            return True
        except HSAUsageException:
            return False

    def resource_is_immutable(self, resource_uuid):
        """
        Whether resource is flagged as immutable

        :type resource_uuid: str
        :param resource_uuid:  resource identifier
        :return: True if resource has been flagged as immutable
        :rtype: bool 
 
        If a resource is immutable:

        1. All write access is denied by all users regardless of privilege. This includes
           resource deletion and any changes to any aspect of the resource. Even owners have no
           privileges other than read over an immutable resource.

        2. Only an administrative user can promote a resource from immutable to mutable.
           Other users must instead copy the resource to a new location.

        The spirit of the immutable flag is that the affected resource's landing page can then safely be
        issued a data citation.
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        meta = self.get_resource_metadata(resource_uuid)
        return meta['immutable']

    def resource_is_published(self, resource_uuid):
        """
        Whether resource is flagged as published

        :type resource_uuid: str
        :param resource_uuid:  resource identifier
        :return: bool: whether resource has been flagged as published
        :rtype: bool 
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        meta = self.get_resource_metadata(resource_uuid)
        return meta['published']

    def resource_is_discoverable(self, resource_uuid):
        """
        Whether resource is flagged as discoverable

        :type resource_uuid: str
        :param resource_uuid:  resource identifier
        :return: bool: whether resource has been flagged as published
        :rtype: bool 
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")
        meta = self.get_resource_metadata(resource_uuid)
        return meta['discoverable']

    def resource_is_public(self, resource_uuid):
        """
        Whether resource is flagged as public

        :type resource_uuid: str
        :param resource_uuid:  resource identifier
        :return: bool: whether resource has been flagged as published
        :rtype: bool 
        """
        meta = self.get_resource_metadata(resource_uuid)
        return meta['public']

    def resource_is_shareable(self, resource_uuid):
        """
        Whether resource is flagged as shareable

        :type resource_uuid: str
        :param resource_uuid:  resource identifier
        :return: bool: whether resource has been flagged as published
        :rtype: bool 
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        meta = self.get_resource_metadata(resource_uuid)
        return meta['shareable']

    ###########################################################
    # user privilege over resources
    ###########################################################
    def __get_privilege_id_from_code(self, code):
        """
        PRIVATE: translate from privilege code to database id

        :type code: str:
        :param code: code for privilege level: own, rw, ro, ns
        :return: privilege_id in database system
        :rtype: int 

        This routine translates a privilege code into an integer. Current privilege codes include:

            own
                owner of resource (1)

            rw
                read-write (with sharing privilege) (2)

            ro
                read-only (with sharing privilege) (3)

            ns
                read-only without privilege to share. (4)

        The privilege level for an object is a minimum of all the privilege levels assigned by different people.

        For example, if

        * one owner assigns ownership privilege and, unbeknownst to this owner,

        * another owner assigns read-only privilege,

        Then the resulting privilege is "owner".

        Note that although these codes are used consistently for privileges over groups and resources,
        there is no reasonable meaning for

        1. group ownership of a resource

        2. no sharing for a group

        Thus, one may not assert these states.
        """
        self.__cur.execute("select privilege_id from privileges where privilege_code=%s", (code,))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("Database integrity violation: "
                                        + "more than one record for a specific privilege code")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['privilege_id']
        else:
            raise HSAUsageException("Privilege code '" + code + "' does not exist")

    ###########################################################
    # I am forced to choose between two alternatives, neither of which is desirable.
    # If I allow something to be owned but overridden, then
    # * I cannot assume that owned implies writeable.
    # * Owned does imply readable.
    # If I have different protections for data than metadata, then
    # * ownership implications are correct but
    # * there is confusion over what to do when.
    # Decision: ownership is handled differently
    ###########################################################

    ###########################################################
    # primitive resource privilege interface does not include the resource-local
    # flags that override user flags for data access. Thus it is a lower-level interface.
    ###########################################################
    def get_user_privilege_over_resource(self, resource_uuid):
        """
        Get privilege code for user over a resource

        :type resource_uuid: str
        :param resource_uuid: uuid of resource
        :return: one of 'own', 'rw', 'ro', 'none' 
        :rtype: str 

        This returns one of the following strings:

            'own'

                User owns this resource

            'rw'

                User can change thsi resource

            'ro'

                User can read but not change this resource

            'none'

                No privilege over resource
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        pnum = self.__get_user_privilege_over_resource(resource_uuid)
        if pnum >= self.__PRIVILEGE_OWN and pnum <= self.__PRIVILEGE_NONE:
            return self.__PRIVILEGE_CODES[pnum-1]
        else:
            raise HSAIntegrityException("Invalid privilege number")

    def __get_user_privilege_over_resource(self, resource_uuid, user_uuid=None):
        """
        Summarize privileges of a user over a resource, without incorporating resource flags

        :type user_uuid: str
        :param resource_uuid: uuid of resource
        :param user_uuid: uuid of user; omit to report on current user
        :return: privilege number 1-4
        :rtype: int 

        The access privileges are the minimum (most powerful) privilege granted by any one user.
        These include:

        1. Privileges granted specifically to the user.

        2. Privileges granted via membership in a group.

        Note: this routine is not subject to access control.
        """
        user_id = self.__get_user_id_from_uuid(user_uuid)
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        return self.__get_user_privilege_over_resource_by_id(resource_id, user_id)

    def __get_user_privilege_over_resource_by_id(self, resource_id, user_id):
        self.__cur.execute("""select user_id, resource_id, privilege_id from user_resource_privilege
                              where user_id=%s and resource_id=%s""",
                           (user_id, resource_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("Database integrity violation: "
                                        + "more than one record for a specific user/resource pair")
        if self.__cur.rowcount > 0:
            data = self.__cur.fetchone()
            # this looks correct!
            # print "privilege_id is ", data['privilege_id']
            priv = data['privilege_id']
            return priv
        else:
            # print "no privilege"
            return self.__PRIVILEGE_NONE  # no privilege

    ###########################################################
    # cumulative resource privilege interface includes resource-local
    # flags that override user flags for data access.
    ###########################################################

    def get_cumulative_user_privilege_over_resource(self, resource_uuid, user_uuid=None):
        """
        Get privilege code for user over a resource

        :type resource_uuid: str
        :param resource_uuid: uuid of resource
        :param user_uuid: uuid of user; omit to report on current user
        :return: one of 'own', 'rw', 'ro', or 'none' 
        :rtype: str 

        This checks for both user resource permissions and resource flags.
        This returns one of the following strings:

            'own'

                User owns this resource

            'rw'

                User can change thsi resource

            'ro'

                User can read but not change this resource

            'none'

                No privilege over resource
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a string")

        pnum = self.__get_cumulative_user_privilege_over_resource(resource_uuid, user_uuid)
        if pnum >= self.__PRIVILEGE_OWN and pnum <= self.__PRIVILEGE_NONE:
            return self.__PRIVILEGE_CODES[pnum-1]
        else:
            raise HSAIntegrityException("Invalid privilege number")

    def __get_cumulative_user_privilege_over_resource(self, resource_uuid, user_uuid=None):
        """
        Summarize privileges of a user over a resource, incorporating resource flags

        :type resource_uuid: str
        :type user_uuid: str
        :param resource_uuid: uuid of resource
        :param user_uuid: uuid of user; omit to report on current user
        :returns: int: privilege number 1-4

        The access privileges are the minimum (most powerful) privilege granted by any one user.
        These include:

        1. Privileges granted specifically to the user.

        2. Privileges granted via membership in a group.

        3. Privileges granted or removed via resource state flags, including

            * immutable: override write access for a resource.

            * public: give read access to everyone.

        This routine will downgrade owner privileges to read-only for immutable resources.
        Thus it is appropriate for use in iRODS, but not in resource metadata manipulation.
        See also __get_user_privilege_over_resource().

        Note: this routine is not subject to access control. Anyone can read anyone else's privileges.
        """
        user_id = self.__get_user_id_from_uuid(user_uuid)
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)

        # This is the query that determines cumulative privilege for a resource. It returns
        # 1 for owner
        # 2 for read/write
        # 3 for read-only
        self.__cur.execute("""select user_id, resource_id, privilege_id from cumulative_user_resource_privilege
                              where user_id=%s and resource_id=%s""",
                           (user_id, resource_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("Database integrity violation: "
                                        + "more than one record for a specific user/resource pair")
        if self.__cur.rowcount > 0:
            data = self.__cur.fetchone()
            # this looks correct!
            # print "privilege_id is ", data['privilege_id']
            priv = data['privilege_id']
            return priv
        else:
            if self.resource_is_public(resource_uuid):  # separate query, to avoid cross product
                return self.__PRIVILEGE_RO
            else:
                # print "no privilege"
                return self.__PRIVILEGE_NONE  # no privilege

    # whether resource is accessible according to a specific code
    def __resource_accessible(self, user_uuid, resource_uuid, code):
        """
        Check if resource is accessible to a specific user in a specific way

        :type user_uuid: str
        :type resource_uuid: str
        :type code: str
        :param user_uuid: user uuid, key to users table
        :param resource_uuid: resource uuid: key to resources table
        :param code: privilege code: key to privileges table
        :return: bool: True if resource is accessible to user in the mode indicated by code
        :rtype: bool 

        This routine checks if a resource is accessible at a given level.
        The codes include:

            own
                ownership

            rw
                read-write

            ro
                read-only

        This is very tricky. This routine returns the protection according to the protection system
        but does not account for flags. If it did, then flagging a resource as immutable would take
        away its owners.

        Actual privilege according to resource flags is accounted for in the routines
        resource_is_readwrite, resource_is_readonly.
        """
        privilege_id = self.__get_privilege_id_from_code(code)
        actual_priv = self.__get_user_privilege_over_resource(resource_uuid, user_uuid)
        if actual_priv <= privilege_id:
            return True
        else:
            return False

    # whether resource is accessible according to a specific code
    def __resource_cumulatively_accessible(self, user_uuid, resource_uuid, code):
        """
        Check if resource is accessible in a specific way, combining both user and resource permissions

        :type user_uuid: str
        :type resource_uuid: str
        :type code: str
        :param user_uuid: user uuid, key to users table
        :param resource_uuid: resource uuid: key to resources table
        :param code: privilege code: key to privileges table
        :return: bool: True if resource is accessible to user in the mode indicated by code
        :rtype: bool 

        This routine checks if a resource is accessible at a given level.
        The codes include:

            own
                ownership

            rw
                read-write

            ro
                read-only

        This is very tricky. This routine returns the protection according to the protection system
        but does not account for flags. If it did, then flagging a resource as immutable would take
        away its owners.

        Actual privilege according to resource flags is accounted for in the routines
        resource_is_readwrite, resource_is_readonly.
        """
        privilege_id = self.__get_privilege_id_from_code(code)
        actual_priv = self.__get_cumulative_user_privilege_over_resource(resource_uuid, user_uuid)
        if actual_priv <= privilege_id:
            return True
        else:
            if privilege_id == 3 and self.resource_is_public(resource_uuid):
                return True
            else:
                return False

    def resource_is_owned(self, resource_uuid, user_uuid=None):
        """
        Check whether a given resource is owned by a specific user

        :type resource_uuid: str
        :type user_uuid: str
        :param resource_uuid: resource identifier for resource to be checked for access
        :param user_uuid: uuid of user whose privileges should be checked; omit to check current user
        :return: bool: True if user owns resource.
        :rtype: bool 

        This routine is a bit strange, because ownership -- unlike read/write and read-only privileges --
        is not subject to overrides from resource flags including 'immutable' and 'public".

        Thus -- in particular -- it is possible for an immutable resource to be *owned but not writeable*.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        return self.__resource_accessible(user_uuid, resource_uuid, 'own')

    def resource_is_readwrite(self, resource_uuid, user_uuid=None):
        """
        Check whether a given resource is read/write to a specific user

        :type resource_uuid: str
        :type user_uuid: str
        :param resource_uuid: resource identifier for resource to be checked for access
        :param user_uuid: uuid of user whose privileges should be checked; omit to check current user
        :return: bool: True if user has readwrite privilege over resource.
        :rtype: bool 

        This is subject to resource override flags including 'immutable' and 'public'.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        return self.__resource_cumulatively_accessible(user_uuid, resource_uuid, 'rw')

    def resource_is_readable(self, resource_uuid, user_uuid=None):
        """
        Check whether a given resource is readable by a specific user

        :type resource_uuid: str
        :type user_uuid: str
        :param resource_uuid: resource identifier for resource to be checked for access
        :param user_uuid: uuid of user whose privileges should be checked; omit to check current user
        :return: bool: True if user has read-only privilege over resource.
        :rtype: bool 

        This is subject to resource override flags including 'immutable' and 'public'.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        return self.__resource_cumulatively_accessible(user_uuid, resource_uuid, 'ro')

    ###########################################################
    # Share a resource with a specific user.
    # CLI: hs_share_resource
    # business logic:
    # we can share a resource with a user
    # - at a privilege that we already enjoy for the resource.
    # - unless your privilege is "ns".
    # - or you have admin privileges.
    # users who shared a resource with another user can downgrade or upgrade that sharing as desired.
    # The sharing privileges for a user are a logical OR of all granted sharing privileges from all sources
    ###########################################################

    def share_resource_with_user(self, resource_uuid, user_uuid, privilege_code='ro'):
        """
        Share a specific resource with a specific user

        :type resource_uuid: str
        :type user_uuid: str
        :type privilege_code: str
        :param resource_uuid: uuid of resource to affect (key to resource table)
        :param user_uuid: login name of user to gain access (key to users table)
        :param privilege_code: privilege to grant (key to privileges table)

        This shares a resource with a user other than self. The current user is implicitly
        the initiator of the sharing.

        This is subject to several restrictions:

        1. A user may not share a resource with self.

        2. A user may not share a resource at a higher privilege level than that held by the user.

        3. A user may only update records created by that user, e.g., to upgrade or downgrade sharing
           privileges for another user.

        4. An administrative user may arbitrarily change sharing parameters.

        """
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        user_id = self.__get_user_id_from_uuid(user_uuid)
        # requested privilege id
        privilege_id = self.__get_privilege_id_from_code(privilege_code)
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        requesting_id = self.__get_user_id_from_uuid(self.get_uuid())

        # access control logic: cannot grant sharing above own privilege
        if not self.user_is_admin(self.get_uuid()):
            if not self.resource_is_owned(resource_uuid) and not self.resource_is_shareable(resource_uuid):
                raise HSAccessException("Resource is not shareable by non-owners")
            # use join to access privilege records
            user_priv = self.__get_user_privilege_over_resource(resource_uuid)
            if user_priv > self.__PRIVILEGE_RO:
                raise HSAccessException("User has no privilege over resource")
            if user_priv > privilege_id:
                raise HSAccessException("User has insufficient privilege over resource")
            if user_uuid == self.get_uuid():
                if self.resource_is_owned(resource_uuid):
                    if self.get_number_of_resource_owners(resource_uuid) == 1:
                        raise HSAccessException("Cannot remove last owner of resource")
        self.__share_resource_with_user(requesting_id, user_id, resource_id, privilege_id)

    def __share_resource_with_user(self, requesting_id, user_id, resource_id, privilege_id):
        """
        Share a resource with a user at a given privilege level.

        :type requesting_id: int
        :type user_id: int
        :type resource_id: int
        :type privilege_id: int
        :param requesting_id: id of requesting user
        :param user_id: user id of user to which to grant privilege
        :param resource_id: resource id to which to grant privilege
        :param privilege_id: privilege to grant

        """
        #  sufficient privileges present to share this resource
        if self.__user_access_to_resource_exists(user_id, resource_id, requesting_id):
            # don't let user remove last owner.
            if self.__get_number_of_resource_owners_by_id(resource_id) > 1 \
                    or self.__get_user_privilege_over_resource_by_id(resource_id, user_id) > 1:
                self.__share_resource_user_update(requesting_id, user_id, resource_id, privilege_id)
            else:
                raise HSAccessException("Cannot remove last resource owner, including self")
        else:
            self.__share_resource_user_add(requesting_id, user_id, resource_id, privilege_id)

    def __user_access_to_resource_exists(self, user_id, resource_id, asserting_user_id):
        """
        PRIVATE: Determine whether there is a record currently sharing the resource, by this user

        :type user_id: int
        :type resource_id: int
        :type asserting_user_id: int
        :param user_id: id of user to gain privilege
        :param resource_id: id of resource on which to grant privilege
        :param asserting_user_id: id of user granting privilege
        :return: True if there is a current record for this triple
        :rtype: bool 

        This is a helper routine for "share_resource_with_user".
        Note: this routine is not subject to access control.
        """
        self.__cur.execute(
            """select privilege_id from user_access_to_resource where user_id=%s
            and resource_id=%s and assertion_user_id=%s""",
            (user_id, resource_id, asserting_user_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific privilege code")
        if self.__cur.rowcount > 0:
            return True
        else:
            return False

    def __share_resource_user_update(self, requesting_id, user_id, resource_id, privilege_id):
        """
        PRIVATE: update a user record

        :type requesting_id: int
        :type user_id: int
        :type resource_id: int
        :type privilege_id: int
        :param requesting_id: user id of requesting user
        :param user_id: user id of affected user
        :param resource_id: resource id of affected resource
        :param privilege_id: privilege id to assign

        This is a helper routine for "share_resource_with_user". If the resource record
        to be updated does not exist, an exception is raised.

        Note: this routine is not subject to access control.
        """
        self.__cur.execute("""update user_access_to_resource set privilege_id = %s,
                              assertion_time=CURRENT_TIMESTAMP
                              where user_id=%s and resource_id=%s and assertion_user_id=%s""",
                           (privilege_id, user_id, resource_id, requesting_id))
        self.__conn.commit()

    def __share_resource_user_add(self, requesting_id, user_id, resource_id, privilege_id):
        """
        PRIVATE: add a user record

        :type requesting_id: int
        :type user_id: int
        :type resource_id: int
        :type privilege_id: int
        :param requesting_id: user id of requesting user
        :param user_id: user id of affected user
        :param resource_id: resource id of affected resource
        :param privilege_id: privilege id to assign

        This is a helper routine for 'share_resource_with_user'. If the resource record
        to be updated does not exist, an exception is raised.

        Note: this routine is not subject to access control.
        """
        self.__cur.execute("""insert into user_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                           (user_id, resource_id, privilege_id, requesting_id))
        self.__conn.commit()

    def unshare_resource_with_user(self,  resource_uuid, user_uuid=None):
        """
        Remove all sharing with user (owner only)

        :type resource_uuid: str
        :type user_uuid: str
        :param resource_uuid: resource to change
        :param user_uuid: user with whom resource is currently shared; omit for current user

        Note: since sharing is cumulative, each user sharing a document with another must separately retract sharing
        before all sharing is removed. It is possible that a user will have several different paths to a resource.

        This routine unshares a resource under three possible conditions; either:
        1. user is admin, or

        2. user owns resource, or

        3. user is the sharing target: one should be able to "forget" a share if necessary

        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        # assert_id = self.__get_user_id_from_uuid(self.get_uuid())
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        user_id = self.__get_user_id_from_uuid(user_uuid)
        if self.user_is_admin(self.get_uuid()) \
                or self.resource_is_owned(resource_uuid) \
                or user_uuid == self.get_uuid():
            if self.get_number_of_resource_owners(resource_uuid) > 1 \
                    or not self.resource_is_owned(resource_uuid, user_uuid):
                self.__cur.execute("""delete from user_access_to_resource where user_id = %s and resource_id = %s""",
                                   (user_id, resource_id))
                self.__conn.commit()
            else:
                raise HSAccessException("Cannot remove only resource owner, including self")
        else:
            raise HSAccessException("Regular user must own resource")

    ###########################################################
    # group privilege
    ###########################################################

    # ##########################################################
    # share a resource with a group of users
    # CLI: hs_share_resource
    # business logic:
    # you can share a resource with a group if
    # - you are in the group and
    # - you have sharing privilege over the resource equal or greater than what you wish to assign or
    # - you are an administrator
    # ##########################################################

    def share_resource_with_group(self, resource_uuid, group_uuid, privilege_code='ro'):
        """
        Share a resource with a group of users

        :type resource_uuid: str
        :type group_uuid: str
        :type privilege_code: str
        :param resource_uuid: the resource to be shared
        :param group_uuid: the group with which to share it: self.get_uuid() must be a member.
        :param privilege_code: the privilege to assign: must be less than or equal to self.get_uuid()'s privilege

        Share a resource with a group as the current user.

        Preconditions:

        1. Current user must be a member of the group, or have administrative privilege.

        2. Current user must have the same or more comprehensive access to the resource than for the share,
           or administrative privilege.

        Postconditions: resource is shared with all members of the group. Privileges changes for all group members
        as individuals, simultaneously.

        This works the same whether this is the first or a subsequent time the resource is shared. A user can
        downgrade or upgrade sharing privileges for a resource at will.

        Note: if a user shares a privilege that is then revoked for that user, the sharing privilege persists
        for the object.  It is possible to downgrade privilege assigned by a user whose privilege has been
        downgraded, but this has not been implemented.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        group_id = self.__get_group_id_from_uuid(group_uuid)
        privilege_id = self.__get_privilege_id_from_code(privilege_code)
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        requesting_id = self.__get_user_id_from_uuid(self.get_uuid())
        # access control logic: cannot grant sharing above own privilege
        if privilege_id == self.__PRIVILEGE_OWN:
            raise HSAUsageException("A group cannot own a resource")
        if not self.user_is_admin(self.get_uuid()):
            if not self.user_in_group(group_uuid, self.get_uuid()):
                raise HSAccessException("User is not a member of the group")
            if not (self.user_is_admin(self.get_uuid())):
                # use join and aggregation to access privilege records
                user_priv_over_group = self.__get_cumulative_user_privilege_over_group(group_uuid)
                if user_priv_over_group >= self.__PRIVILEGE_RO:
                    raise HSAccessException("User has no group sharing privileges")
                user_priv_over_resource = self.__get_user_privilege_over_resource(resource_uuid)
                if user_priv_over_resource > privilege_id:
                    raise HSAccessException("User has inadequate access to resource")
        # sufficient privileges present to share this resource
        if self.__group_access_to_resource_exists(requesting_id,  resource_id, group_id):
            self.__share_resource_group_update(requesting_id, group_id, resource_id, privilege_id)
        else:
            self.__share_resource_group_add(requesting_id, group_id, resource_id, privilege_id)

    def __group_access_to_resource_exists(self, requesting_id, resource_id, group_id):
        """
        PRIVATE: Check whether there is already a privilege record for asserting user, group, and resource

        :type group_id: int
        :type resource_id: int
        :type requesting_id: int
        :param group_id: internal group id of affected group
        :param resource_id: internal resource id of affected resource
        :param requesting_id: internal id of user requesting change

        This is a helper routine for 'share_resource_with_group'.
        """
        self.__cur.execute(
            """select privilege_id from group_access_to_resource where group_id=%s
            and resource_id=%s and assertion_user_id=%s""",
            (group_id, resource_id, requesting_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a specific group resource access tuple")
        if self.__cur.rowcount > 0:
            return True
        else:
            return False

    def __share_resource_group_update(self, requesting_id, group_id, resource_id, privilege_id):
        """
        PRIVATE: update group sharing record for a resource

        :type requesting_id: int
        :type group_id: int
        :type resource_id: int
        :type privilege_id: int
        :param requesting_id: id of requesting user
        :param group_id: id of group to modify
        :param resource_id: id of resource to modify
        :param privilege_id: privilege to assign

        This is a helper routine for 'share_resource_with_group'.

        The group sharing record must exist or an exception is raised.
        """
        self.__cur.execute("""update group_access_to_resource set privilege_id = %s,
                              assertion_time=CURRENT_TIMESTAMP where group_id=%s
                              and resource_id=%s and assertion_user_id=%s""",
                           (privilege_id, group_id, resource_id, requesting_id))
        self.__conn.commit()

    def __share_resource_group_add(self, requesting_id, group_id, resource_id, privilege_id):
        """
        PRIVATE: add a new group sharing record for a resource

        :type requesting_id: int
        :type group_id: int
        :type resource_id: int
        :type privilege_id: int
        :param requesting_id: id of requesting user
        :param group_id: id of group to modify
        :param resource_id: id of resource to modify
        :param privilege_id: privilege to assign

        This is a helper routine for 'share_resource_with_group'.

        The group sharing record must not exist or an exception is raised.
        """
        self.__cur.execute("""insert into group_access_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                           (group_id, resource_id, privilege_id, requesting_id))
        self.__conn.commit()

    def unshare_resource_with_group(self, resource_uuid, group_uuid):
        """
        Remove all sharing with user (owner or administrator only)

        :type resource_uuid: str
        :type group_uuid: str
        :param resource_uuid: resource to change
        :param group_uuid: group with whom resource is currently potentially shared

        Only a group owner or administrator may revoke all privileges over a resource.  This
        includes all grants of privilege no matter what the source within the group.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        # assert_id = self.__get_user_id_from_uuid(self.get_uuid())
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        if self.user_is_admin(self.get_uuid()) or self.group_is_owned(group_uuid):
            self.__cur.execute("""delete from group_access_to_resource where group_id = %s and resource_id=%s""",
                               (group_id, resource_id))
            self.__conn.commit()
        else:
            raise HSAccessException("Regular user must own group")

    ###########################################################
    # group membership
    ###########################################################
    # refactored to remove duplication between group privilege and membership
    def user_in_group(self, group_uuid, user_uuid=None):
        """
        Check whether a user is a member of a group

        :type user_uuid: str
        :type group_uuid: str
        :param user_uuid: uuid of a valid user, omit to check current user
        :param group_uuid: group uuid of a valid group
        :return: bool: True if the uuid is in the group
        :rtype: bool 

        Note: this uses user_group_privilege whereas access uses cumulative_user_group_privilege.
        The reason for this is that membership must not account for public groups (which is most of them).
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        self.__cur.execute("""select privilege_id from user_group_privilege
                              where user_id=%s and group_id=%s""",
                           (user_id, group_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one group membership record for a user and group")
        if self.__cur.rowcount > 0:
            return True
        else:
            return False

    # # OLD VERSION with specific user_membership_in_group table
    # # REPLACED with conflation of privilege with membership
    # # to avoid potential data skwews
    # def user_in_group(self, group_uuid, user_uuid=None):
    #     """
    #     Check whether a user is a member of a group
    #
    #     :type user_uuid: str
    #     :type group_uuid: str
    #     :param user_uuid: uuid of a valid user
    #     :param group_uuid: group uuid of a valid group
    #     :return: True if the uuid is in the group
    #     """
    #     if user_uuid is None:
    #         user_uuid = self.get_uuid()
    #     if type(user_uuid) is not str:
    #         raise HSAUsageException("user_uuid is not a string")
    #     user_id = self.__get_user_id_from_uuid(user_uuid)
    #     group_id = self.__get_group_id_from_uuid(group_uuid)
    #     self.__cur.execute("""select id from user_membership_in_group where user_id=%s and group_id=%s""",
    #                       (user_id, group_id))
    #     if self.__cur.rowcount > 1:
    #         raise HSAIntegrityException("More than one group membership record for a user and group")
    #     if self.__cur.rowcount > 0:
    #         return True
    #     else:
    #         return False
    #
    # def assert_user_in_group(self, group_uuid, user_uuid=None):
    #     """
    #     Add a user to a group if not present already
    #
    #     :type user_uuid: str
    #     :type group_uuid: str
    #     :param user_uuid: user to be added to the group
    #     :param group_uuid: group to which to add user
    #     :return:
    #     """
    #     if user_uuid is None:
    #         user_uuid = self.get_uuid()
    #     if type(user_uuid) is not str:
    #         raise HSAUsageException("user_uuid is not a string")
    #     # if not self.user_is_active(self.get_uuid()):
    #     #     raise HSAUsageException("User login '"+self.__get_user_login_from_uuid(self.get_uuid())
    #     #     +"' is not active")
    #     if not self.user_exists(user_uuid):
    #         raise HSAUsageException("User uuid '"+user_uuid+"' does not exist")
    #     if not self.user_is_active(user_uuid):
    #         raise HSAccessException("User is not active")
    #     if not self.group_is_readwrite(group_uuid, self.get_uuid()):
    #         raise HSAccessException("Group is not writeable to user")
    #     self.__assert_user_in_group(group_uuid, user_uuid)
    #
    # # need this in certain system routines to avoid protection chicken-and-egg problems
    # def __assert_user_in_group(self, group_uuid, user_uuid=None):
    #     """
    #     Override protection scheme to insert first user into group
    #
    #     :param user_uuid:
    #     :param group_uuid:
    #     :return:
    #     """
    #     if user_uuid is None:
    #         user_uuid = self.get_uuid()
    #     if type(user_uuid) is not str:
    #         raise HSAUsageException("user_uuid is not a string")
    #     requesting_id = self.__get_user_id_from_uuid(self.get_uuid())
    #     user_id = self.__get_user_id_from_uuid(user_uuid)
    #     group_id = self.__get_group_id_from_uuid(group_uuid)
    #     if not (self.user_in_group(group_uuid, user_uuid)):
    #         self.__cur.execute("insert into user_membership_in_group VALUES (DEFAULT, %s, %s, %s, DEFAULT)",
    #                           (user_id, group_id, requesting_id))
    #         self.__conn.commit()
    #     # self.share_group_with_user(group_uuid, user_uuid, 'ro')
    #
    # # CLI: hs_remove_user_from_group
    # def retract_user_from_group(self, user_uuid, group_uuid):
    #     """
    #     Remove a user from a group if not absent already
    #
    #     :type user_uuid: str
    #     :type group_uuid: str
    #     :param user_uuid: user to be removed from the group
    #     :param group_uuid: group from which to remove user
    #     :return:
    #     """
    #
    #     user_id = self.__get_user_id_from_uuid(user_uuid)
    #     group_id = self.__get_group_id_from_uuid(group_uuid)
    #
    #     # for now, let people remove themselves
    #     if self.get_uuid() == user_uuid and self.user_in_group(group_uuid, user_uuid):
    #         self.__cur.execute("delete from user_membership_in_group where user_id=%s and group_id=%s",
    #                           (user_id, group_id))
    #     else:
    #         raise HSAccessException("User must be administrator or group owner")
    #     self.unshare_group_with_user(group_uuid, user_uuid)

    ###########################################################
    # group access
    # in current version this is synonymous with membership
    ###########################################################
    ###########################################################
    # cumulative resource privilege interface includes group-local
    # flags that override user flags for data access.
    ###########################################################
    def get_cumulative_user_privilege_over_group(self, group_uuid, user_uuid=None):
        """
        Get privilege code for user over a group

        :param group_uuid:
        :type group_uuid: str
        :param group_uuid: uuid of group
        :param user_uuid: uuid of user; omit to report on current user
        :return: one of 'own', 'rw', 'ro', 'none' 
        :rtype: str 

        This checks for both user group permissions and group flags, including group_public.
        This returns one of the following strings:

            'own'

                User owns this resource

            'rw'

                User can change this resource

            'ro'

                User can read but not change this resource

            'none'

                No privilege over resource
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")

        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        pnum = self.__get_cumulative_user_privilege_over_group(group_uuid, user_uuid)
        if pnum >= self.__PRIVILEGE_OWN and pnum <= self.__PRIVILEGE_NONE:
            return self.__PRIVILEGE_CODES[pnum-1]
        else:
            raise HSAIntegrityException("Invalid privilege number")

    def get_user_privilege_over_group(self, group_uuid, user_uuid=None):
        """
        Get privilege code for user over a group

        :param group_uuid:
        :type group_uuid: str
        :param group_uuid: uuid of group
        :param user_uuid: uuid of user; omit to report on current user
        :return: one of 'own', 'rw', 'ro', or 'none' 
        :rtype: str 

        This checks for both user group permissions and group flags, including group_public.
        This returns one of the following strings:

            'own'

                User owns this resource

            'rw'

                User can change this resource

            'ro'

                User can read but not change this resource

            'none'

                No privilege over resource
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        pnum = self.__get_user_privilege_over_group(group_uuid, user_uuid)
        if pnum >= self.__PRIVILEGE_OWN and pnum <= self.__PRIVILEGE_NONE:
            return self.__PRIVILEGE_CODES[pnum-1]
        else:
            raise HSAIntegrityException("Invalid privilege number")

    # utilize a join view to summarize user privilege
    def __get_cumulative_user_privilege_over_group(self, group_uuid, user_uuid=None):
        """
        Get the privilege that is specified for a user over a specific group
        :type user_uuid: str
        :type group_uuid: str
        :param user_uuid: uuid of user for which to obtain privilege
        :param group_uuid: group to which to allow access
        :return: privilege code 1-4
        :rtype: int

        This returns the cumulative user privilege over a group, including whether the group is public if the
        user is not a member. This is a union of privileges from membership and the group public flag.
        Note that there is no ownership conflict in this case because a group cannot be made immutable.
        """
        user_id = self.__get_user_id_from_uuid(user_uuid)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        # THIS IS THE QUERY THAT DETERMINES GROUP ACCESS
        # SAME CODES AS FOR USER PRIVILEGE
        self.__cur.execute("""select privilege_id from cumulative_user_group_privilege
                              where user_id=%s and group_id=%s""",
                           (user_id, group_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one user group privilege tuple for one granting user")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['privilege_id']
        else:
            if self.group_is_public(group_uuid):  # separate query, to avoid cross product
                return self.__PRIVILEGE_RO
            else:
                return self.__PRIVILEGE_NONE  # no privilege

    # utilize a join view to summarize user privilege
    def __get_user_privilege_over_group(self, group_uuid, user_uuid=None):
        """
        Get the privilege that is specified for a user over a specific group
        :type user_uuid: str
        :type group_uuid: str
        :param user_uuid: uuid of user for which to obtain privilege
        :param group_uuid: group to which to allow access
        :return: privilege number 1-4
        :rtype: int

        This returns the cumulative user privilege over a group, including whether the group is public if the
        user is not a member. This is a union of privileges from membership and the group public flag.
        Note that there is no ownership conflict in this case because a group cannot be made immutable.
        """
        user_id = self.__get_user_id_from_uuid(user_uuid)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        # THIS IS THE QUERY THAT DETERMINES GROUP ACCESS
        # SAME CODES AS FOR USER PRIVILEGE
        self.__cur.execute("""select privilege_id from cumulative_user_group_privilege
                              where user_id=%s and group_id=%s""",
                           (user_id, group_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one user group privilege tuple for one granting user")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['privilege_id']
        else:
            return self.__PRIVILEGE_NONE  # no privilege

    # utility routine returns numeric code for privilege
    def __group_cumulatively_accessible(self, user_uuid, group_uuid, code):
        """
        PRIVATE: check whether a group is accessible to a user
        :type user_uuid: str
        :type group_uuid: str
        :type code: str
        :param user_uuid: uuid of user for whom to check privilege (key to users table)
        :param group_uuid: uuid of group for which to check privilege (key to groups table)
        :param code: privilege code (key to privileges table)
        :return: bool: True if group is accessible to user in the provided mode
        :rtype: bool 
        """
        requested_priv = self.__get_privilege_id_from_code(code)
        actual_priv = self.__get_cumulative_user_privilege_over_group(group_uuid, user_uuid)
        # print user_uuid, group_uuid, "requested priv=", requested_priv, "actual priv=", actual_priv
        if actual_priv <= requested_priv:
            return True
        else:
            if requested_priv == 3 and self.group_is_public(group_uuid):
                return True
            else:
                return False

    # can remove group and disinvite group members.
    def group_is_owned(self, group_uuid, user_uuid=None):
        """
        Check whether a group is owned by a user

        :type user_uuid: str
        :type group_uuid: str
        :param user_uuid: uuid of user to check
        :param group_uuid: group uuid of group to check
        :return: bool: True if group uuid is owned by user uuid
        :rtype: bool 
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        return self.__group_cumulatively_accessible(user_uuid, group_uuid, 'own')

    # can invite members to group
    def group_is_readwrite(self, group_uuid, user_uuid=None):
        """
        Check whether a group is owned by a user

        :type user_uuid: str
        :type group_uuid: str
        :param user_uuid: uuid of user to check
        :param group_uuid: group uuid of group to check
        :return: bool: True if group uuid is read/write to user uuid
        :rtype: bool 
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        return self.__group_cumulatively_accessible(user_uuid, group_uuid, 'rw')

    # minimal group membership: can see members but cannot add/invite them
    def group_is_readable(self, group_uuid, user_uuid=None):
        """
        Check whether a group is readable by a user

        :type user_uuid: str
        :type group_uuid: str
        :param user_uuid: uuid of user to check
        :param group_uuid: group uuid of group to check
        :return: bool: True if group uuid is readable by user uuid
        :rtype: bool 
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        return self.__group_cumulatively_accessible(user_uuid, group_uuid, 'ro')

    # CLI: hs invite ....
    def invite_user_to_group(self, group_uuid, user_uuid, privilege_code='ro'):
        """
        Invite a user into a group. The user must accept in a separate step.

        :param group_uuid:
        :param user_uuid:
        :param privilege_code:
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        privilege_id = self.__get_privilege_id_from_code(privilege_code)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        requesting_id = self.__get_user_id_from_uuid(self.get_uuid())
        # sanity logic: no such thing as 'ns' access.
        # if privilege_code == 'ns':
        #    raise HSAccessException("privilege 'readable without sharing' does not apply to groups")
        # access control logic: cannot grant sharing above own privilege
        if not (self.user_is_admin(self.get_uuid())):
            # use join to access privilege records
            user_priv = self.__get_cumulative_user_privilege_over_group(group_uuid)
            if user_priv >= self.__PRIVILEGE_RO:  # read-only or no-sharing
                raise HSAccessException("User does not have permission to invite members")
            if user_priv > privilege_id:
                raise HSAccessException("User has insufficient privilege over group")
            if user_uuid == self.get_uuid():
                raise HSAccessException("Cannot invite self to group")
        # sufficient privileges present to share this resource
        if self.__user_invite_to_group_exists(requesting_id, group_id, user_id):
            self.__invite_group_user_update(requesting_id, user_id, group_id, privilege_id)
        else:
            self.__invite_group_user_add(requesting_id, user_id, group_id, privilege_id)

    def __invite_group_user_update(self, requesting_id, user_id, group_id, privilege_id):
        """
        PRIVATE: update user access to a group

        :type requesting_id: int
        :type user_id: int
        :type group_id: int
        :type privilege_id: int
        :param requesting_id: id of user requesting change
        :param user_id: id of user to be enabled
        :param group_id: id of group to be modified
        :param privilege_id: id of privilege to be installed
        """
        self.__cur.execute("""update user_invitations_to_group set privilege_id = %s,
                              assertion_time=CURRENT_TIMESTAMP
                              where user_id=%s and group_id=%s
                                and assertion_user_id=%s""",
                           (privilege_id, user_id, group_id, requesting_id))
        self.__conn.commit()

    def __invite_group_user_add(self, requesting_id, user_id, group_id, privilege_id):
        """
        PRIVATE: add new user access for a group

        :type requesting_id: int
        :type user_id: int
        :type group_id: int
        :type privilege_id: int
        :param requesting_id: int: id of user requesting change
        :param user_id: int: id of user to be enabled
        :param group_id: int: id of group to be modified
        :param privilege_id: int: id of privilege to be installed
        """
        self.__cur.execute("""insert into user_invitations_to_group values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                           (user_id, group_id, privilege_id, requesting_id))
        self.__conn.commit()

    # determine whether an invitation exists already
    def __user_invite_to_group_exists(self, requesting_id, group_id, user_id):
        """
        Test whether there is an access record for a specific user, group, and asserting user

        :type user_id: int
        :type group_id: int
        :type requesting_id: int
        :param user_id: user id of user who needs privilege
        :param group_id: group id of group to which privilege will be assigned
        :param requesting_id: user id of user assigning privilege
        :return: True if the invitation exists. 
        :rtype: bool 
        """
        self.__cur.execute("""select privilege_id from user_invitations_to_group
                              where user_id=%s and group_id=%s
                                and assertion_user_id=%s""",
                           (user_id, group_id, requesting_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a group privilege tuple")
        if self.__cur.rowcount > 0:
            return True
        else:
            return False

    def __get_privilege_from_group_invite(self, requesting_id, user_id, group_id):
        """
        Test whether there is an access record for a specific user, group, and asserting user

        :type user_id: int
        :type group_id: int
        :type requesting_id: int
        :param user_id: user id of user who needs privilege
        :param group_id: group id of group to which privilege will be assigned
        :param requesting_id: user id of user assigning privilege
        :return: privilege code 1-4
        :rtype: int 
        """
        self.__cur.execute(
            """select privilege_id from user_invitations_to_group where user_id=%s and group_id=%s
            and assertion_user_id=%s""",
            (user_id, group_id, requesting_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a group invitation")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['privilege_id']
        else:
            raise HSAccessException("No group invitation for user")

    # a user can only revoke one's own invitations
    # CLI: hs uninvite ....
    def uninvite_user_to_group(self, group_uuid, user_uuid):
        """
        Uninvite a user the current user invited; does not undo other invitations

        Revoke an invitation to join a group
        :param group_uuid: uuid of group
        :param user_uuid: uuid of user
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        requesting_id = self.__get_user_id_from_uuid(self.get_uuid())
        self.__uninvite_user_to_group(requesting_id, group_id, user_id)

    def __uninvite_user_to_group(self, requesting_id, group_id, user_id):
        if self.__user_invite_to_group_exists(requesting_id, group_id, user_id):
            self.__cur.execute("""delete from user_invitations_to_group where user_id=%s
                               and group_id=%s and assertion_user_id=%s""",
                               (user_id, group_id, requesting_id))
            self.__conn.commit()

    # CLI hs ls invitations
    def get_group_invitations_for_user(self, user_uuid=None):
        """
        Get a list of invitations to join groups that can be accepted or refused

        :type user_uuid: str
        :param user_uuid: uuid of user; omit for current user.
        :return: Dict of group invitations. 
        :rtype: Dict 

        This is from the point of view of the invited user.
        List group invitations in the form::

            {
                'group_uuid': {uuid of group},
                'group_name': {name of group},
                'group_privilege': {privilege_code},
                'inviting_user_uuid': {uuid of inviting user},
                'inviting_user_name': {name of inviting user},
                'inviting_user_login': {login of inviting user}
            }

        Note: this has been refactored to have a single level of dict objects rather than two.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("""select g.group_uuid, g.group_name, p.privilege_code,
                              a.user_uuid, a.user_name, a.user_login
                              from user_invitations_to_group i
                              left join groups g on i.group_id=g.group_id
                              left join users u on u.user_id = i.user_id
                              left join users a on a.user_id = i.assertion_user_id
                              left join privileges p on p.privilege_id=i.privilege_id
                              where u.user_uuid=%s
                              order by i.assertion_time desc""",
                           (user_uuid,))
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'group_uuid': row['group_uuid'],
                        'group_name': row['group_name'],
                        'group_privilege': row['privilege_code'],
                        'inviting_user_uuid': row['user_uuid'],
                        'inviting_user_name': row['user_name'],
                        'inviting_user_login': row['user_login']}]
        return result

    # CLI hs ls invitations
    def get_group_invitations_sent_by_user(self, user_uuid=None):
        """
        Get a list of invitations to join groups that can be uninvited

        :type user_uuid: str
        :param user_uuid: uuid of user; omit for current user.
        :return: Dict of invitations sent by a user 
        :rtype: Dict 

        This is from the point of view of the inviting user. List group invitations in the form::

            {
                'group_uuid': {uuid of group},
                'group_name': {name of group},
                'group_privilege': {privilege_code},
                'inviting_user_uuid': {uuid of inviting user},
                'inviting_user_name': {name of inviting user},
                'inviting_user_login': {login of inviting user}
            }

        Note: this has been refactored to have a single level of dict objects rather than two.
        Note: this has been refactored to report on a single group object
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("""select u.user_uuid, u.user_name, u.user_login,
                                     g.group_uuid, g.group_name,
                                     p.privilege_code,
                                     a.user_uuid, a.user_name, a.user_login
                              from user_invitations_to_group i
                              left join groups g on i.group_id=g.group_id
                              left join users u on u.user_id = i.user_id
                              left join users a on a.user_id = i.assertion_user_id
                              left join privileges p on p.privilege_id=i.privilege_id
                              where a.user_uuid=%s
                              order by i.assertion_time desc""",
                           (user_uuid,))
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'group_uuid': row['group_uuid'],
                        'group_name': row['group_name'],
                        'group_privilege': row['privilege_code'],
                        'user_uuid': row['user_uuid'],
                        'user_name': row['user_name'],
                        'user_login': row['user_login'],
                        'inviting_user_uuid': row['user_uuid'],
                        'inviting_user_name': row['user_name'],
                        'inviting_user_login': row['user_login']}]
        return result

    # CLI: hs accept ...
    def accept_invitation_to_group(self, group_uuid, host_uuid):
        """
        Accept an invitation to join a group

        :type group_uuid: str
        :type host_uuid: str
        :param group_uuid: uuid of group for which to accept invitation
        :param host_uuid: user uuid of person who invited you

        Accept an invitation to a group previously made by another user via
        'invite_user_to_group'
        """
        if not (type(host_uuid) is unicode or type(host_uuid) is str):
            raise HSAUsageException("host_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(self.get_uuid())
        group_id = self.__get_group_id_from_uuid(group_uuid)
        requesting_id = self.__get_user_id_from_uuid(host_uuid)
        privilege_id = self.__get_privilege_from_group_invite(requesting_id, user_id, group_id)
        if self.__user_invite_to_group_exists(requesting_id, group_id, user_id):
            self.__share_group_with_user(requesting_id, user_id, group_id, privilege_id)
            # remove invitation after acting on it
            self.__uninvite_user_to_group(requesting_id, group_id, user_id)
        else:
            raise HSAccessException("No group invitation for user")

    # CLI: hs refuse
    def refuse_invitation_to_group(self, group_uuid, host_uuid):
        """
        Refuse an invitation to join a group

        :param group_uuid:
        :param host_uuid: user uuid of person who invited

        Refuse an invitation created with 'invite_user_to_group'.
        """
        if not (type(host_uuid) is unicode or type(host_uuid) is str):
            raise HSAUsageException("host_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(self.get_uuid())
        group_id = self.__get_group_id_from_uuid(group_uuid)
        requesting_id = self.__get_user_id_from_uuid(host_uuid)
        if self.__user_invite_to_group_exists(requesting_id, group_id, user_id):
            # remove invitation without acting on it
            self.__uninvite_user_to_group(requesting_id, group_id, user_id)
        else:
            raise HSAccessException("No group invitation for user")

    ################################################
    # resource sharing invitations
    #################################################
        # CLI: hs invite ....
    def invite_user_to_resource(self, resource_uuid, user_uuid, privilege_code='ro'):
        """
        Invite a user into a resource. The user must accept in a separate step.

        :param resource_uuid:
        :param user_uuid:
        :param privilege_code:
        """
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        user_id = self.__get_user_id_from_uuid(user_uuid)
        privilege_id = self.__get_privilege_id_from_code(privilege_code)
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        requesting_id = self.__get_user_id_from_uuid(self.get_uuid())
        # sanity logic: no such thing as 'ns' access.
        # if privilege_code == 'ns':
        #    raise HSAccessException("privilege 'readable without sharing' does not apply to resources")
        # access control logic: cannot grant sharing above own privilege
        if not (self.user_is_admin(self.get_uuid())):
            # use join to access privilege records
            user_priv = self.__get_cumulative_user_privilege_over_resource(resource_uuid)
            if user_priv >= self.__PRIVILEGE_RO:  # read-only or no-sharing
                raise HSAccessException("User does not have permission to invite members")
            if user_priv > privilege_id:
                raise HSAccessException("User has insufficient privilege over resource")
            if self.get_uuid() == user_uuid:
                raise HSAccessException("Cannot invite self to resource")
        # sufficient privileges present to share this resource
        if self.__user_invite_to_resource_exists(requesting_id, resource_id, user_id):
            self.__invite_resource_user_update(requesting_id, user_id, resource_id, privilege_id)
        else:
            self.__invite_resource_user_add(requesting_id, user_id, resource_id, privilege_id)

    def __invite_resource_user_update(self, requesting_id, user_id, resource_id, privilege_id):
        """
        PRIVATE: update user access to a resource

        :type requesting_id: int
        :type user_id: int
        :type resource_id: int
        :type privilege_id: int
        :param requesting_id: id of user requesting change
        :param user_id: id of user to be enabled
        :param resource_id: id of resource to be modified
        :param privilege_id: id of privilege to be installed
        """
        self.__cur.execute("""update user_invitations_to_resource set privilege_id = %s,
                              assertion_time=CURRENT_TIMESTAMP
                              where user_id=%s and resource_id=%s
                                and assertion_user_id=%s""",
                           (privilege_id, user_id, resource_id, requesting_id))
        self.__conn.commit()

    def __invite_resource_user_add(self, requesting_id, user_id, resource_id, privilege_id):
        """
        PRIVATE: add new user access for a resource

        :type requesting_id: int
        :type user_id: int
        :type resource_id: int
        :type privilege_id: int
        :param requesting_id: int: id of user requesting change
        :param user_id: int: id of user to be enabled
        :param resource_id: int: id of resource to be modified
        :param privilege_id: int: id of privilege to be installed
        """
        self.__cur.execute("""insert into user_invitations_to_resource values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                           (user_id, resource_id, privilege_id, requesting_id))
        self.__conn.commit()

    # determine whether an invitation exists already
    def __user_invite_to_resource_exists(self, requesting_id, resource_id, user_id):
        """
        Test whether there is an access record for a specific user, resource, and asserting user

        :type user_id: int
        :type resource_id: int
        :type requesting_id: int
        :param user_id: user id of user who needs privilege
        :param resource_id: resource id of resource to which privilege will be assigned
        :param requesting_id: user id of user assigning privilege
        :return: True if there is already an invitation to use a resource. 
        :rtype: bool 
        """
        self.__cur.execute("""select privilege_id from user_invitations_to_resource
                              where user_id=%s and resource_id=%s
                                and assertion_user_id=%s""",
                           (user_id, resource_id, requesting_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a resource privilege tuple")
        if self.__cur.rowcount > 0:
            return True
        else:
            return False

    def __get_privilege_from_resource_invite(self, requesting_id, user_id, resource_id):
        """
        Test whether there is an access record for a specific user, resource, and asserting user

        :type user_id: int
        :type resource_id: int
        :type requesting_id: int
        :param user_id: user id of user who needs privilege
        :param resource_id: resource id of resource to which privilege will be assigned
        :param requesting_id: user id of user assigning privilege
        :return: privilege code 1-4
        :rtype: int 
        """
        self.__cur.execute(
            """select privilege_id from user_invitations_to_resource where user_id=%s and resource_id=%s
            and assertion_user_id=%s""",
            (user_id, resource_id, requesting_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a resource invitation")
        if self.__cur.rowcount > 0:
            return self.__cur.fetchone()['privilege_id']
        else:
            raise HSAccessException("No resource invitation for user")

    # a user can only revoke one's own invitations
    # CLI: hs uninvite ....
    def uninvite_user_to_resource(self, resource_uuid, user_uuid):
        """
        Uninvite a user the current user invited; does not undo other invitations

        Revoke an invitation to join a resource
        :param resource_uuid: uuid of resource
        :param user_uuid: uuid of user
        """
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        user_id = self.__get_user_id_from_uuid(user_uuid)
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        requesting_id = self.__get_user_id_from_uuid(self.get_uuid())
        self.__uninvite_user_to_resource(requesting_id, resource_id, user_id)

    def __uninvite_user_to_resource(self, requesting_id, resource_id, user_id):
        if self.__user_invite_to_resource_exists(requesting_id, resource_id, user_id):
            self.__cur.execute("""delete from user_invitations_to_resource where user_id=%s
                              and resource_id=%s and assertion_user_id=%s""",
                               (user_id, resource_id, requesting_id))
            self.__conn.commit()

    # CLI hs ls invitations
    def get_resource_invitations_for_user(self, user_uuid=None):
        """
        Get a list of invitations to join resources that can be accepted or refused

        :type user_uuid: str
        :param user_uuid: uuid of user; omit for current user.
        :return: Dict of resource invitations. 
        :rtype: Dict 

        This is from the point of view of the invited user.
        List resource invitations in the form::

            {
                'resource_uuid': {uuid of resource},
                'resource_title': {name of resource},
                'resource_privilege': {privilege_code},
                'inviting_user_uuid': {uuid of inviting user},
                'inviting_user_name': {name of inviting user},
                'inviting_user_login': {login of inviting user}
            }

        Note: this has been refactored to have a single level of dict objects rather than two.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("""select g.resource_uuid, g.resource_title, p.privilege_code, a.user_uuid, a.user_name, a.user_login
                              from user_invitations_to_resource i
                              left join resources g on i.resource_id=g.resource_id
                              left join users u on u.user_id = i.user_id
                              left join users a on a.user_id = i.assertion_user_id
                              left join privileges p on p.privilege_id=i.privilege_id
                              where u.user_uuid=%s
                              order by i.assertion_time desc""",
                           (user_uuid,))
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'resource_uuid': row['resource_uuid'],
                        'resource_title': row['resource_title'],
                        'resource_privilege': row['privilege_code'],
                        'inviting_user_uuid': row['user_uuid'],
                        'inviting_user_name': row['user_name'],
                        'inviting_user_login': row['user_login']}]
        return result

    # CLI hs ls invitations
    def get_resource_invitations_sent_by_user(self, user_uuid=None):
        """
        Get a list of invitations to join resources that can be uninvited

        :type user_uuid: str
        :param user_uuid: uuid of user; omit for current user.
        :return: Dict of invitations sent by user. 
        :rtype: Dict 

        This is from the point of view of the inviting user. List resource invitations in the form::

            {
                'resource_uuid': {uuid of resource},
                'resource_title': {name of resource},
                'resource_privilege': {privilege_code},
                'inviting_user_uuid': {uuid of inviting user},
                'inviting_user_name': {name of inviting user},
                'inviting_user_login': {login of inviting user}
            }

        Note: this has been refactored to have a single level of dict objects rather than two.

        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        self.__cur.execute("""select g.resource_uuid, g.resource_title, p.privilege_code, u.user_uuid, u.user_name, u.user_login
                              from user_invitations_to_resource i
                              left join resources g on i.resource_id=g.resource_id
                              left join users u on u.user_id = i.user_id
                              left join users a on a.user_id = i.assertion_user_id
                              left join privileges p on p.privilege_id=i.privilege_id
                              where i.assertion_user_id=%s
                              order by i.assertion_time desc""",
                           (user_uuid,))
        rows = self.__cur.fetchall()
        result = []
        for row in rows:
            result += [{'resource_uuid': row['resource_uuid'],
                        'resource_title': row['resource_title'],
                        'resource_privilege': row['privilege_code'],
                        'inviting_user_uuid': row['user_uuid'],
                        'inviting_user_name': row['user_name'],
                        'inviting_user_login': row['user_login']}]
        return result

    # CLI: hs accept ...
    def accept_invitation_to_resource(self, resource_uuid, host_uuid):
        """
        Accept an invitation to join a resource

        :type resource_uuid: str
        :type host_uuid: str
        :param resource_uuid: uuid of resource for which to accept invitation
        :param host_uuid: user uuid of person who invited you

        Accept an invitation to a resource previously made by another user via
        'invite_user_to_resource'
        """
        if not (type(host_uuid) is unicode or type(host_uuid) is str):
            raise HSAUsageException("host_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        user_id = self.__get_user_id_from_uuid(self.get_uuid())
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        requesting_id = self.__get_user_id_from_uuid(host_uuid)
        privilege_id = self.__get_privilege_from_resource_invite(requesting_id, user_id, resource_id)
        if self.__user_invite_to_resource_exists(requesting_id, resource_id, user_id):
            self.__share_resource_with_user(requesting_id, user_id, resource_id, privilege_id)
            # remove invitation after acting on it
            self.__uninvite_user_to_resource(requesting_id, resource_id, user_id)
        else:
            raise HSAccessException("No resource invitation for user")

    # CLI: hs refuse
    def refuse_invitation_to_resource(self, resource_uuid, host_uuid):
        """
        Refuse an invitation to join a resource

        :param resource_uuid:
        :param host_uuid: user uuid of person who invited

        Refuse an invitation created with 'invite_user_to_resource'.
        """
        if not (type(host_uuid) is unicode or type(host_uuid) is str):
            raise HSAUsageException("host_uuid is not a unicode or str")
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        user_id = self.__get_user_id_from_uuid(self.get_uuid())
        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        requesting_id = self.__get_user_id_from_uuid(host_uuid)
        if self.__user_invite_to_resource_exists(requesting_id, resource_id, user_id):
            # remove invitation without acting on it
            self.__uninvite_user_to_resource(requesting_id, resource_id, user_id)
        else:
            raise HSAccessException("No resource invitation for user")

    #  for now, couple group membership with group privilege
    # self.assert_user_in_group(group_uuid, user_uuid)
    def share_group_with_user(self, group_uuid, user_uuid, privilege_code='ro'):
        """
        DEPRECATED: Attempt to share a group with a user: this allows read/write to the group membership list

        :type group_uuid: str
        :type user_uuid: str
        :type privilege_code: str
        :param group_uuid: group identifier of group to which privilege should be assigned
        :param user_uuid: uuid of user to whom privilege should be granted
        :param privilege_code: privilege to be granted.

        This routine has been replaced by the invite/accept/refuse/uninvite interface, including:
        * invite_user_to_group (for inviter)
        * uninvite_user_to_group (for inviter)
        * accept_invitation_to_group (for invitee)
        * refuse_invitation_to_group (for invitee)
        * get_invitations_to_group (for invitee)

        This is a direct sharing of a group without user permission.

        Preconditions:

        1. current user must have equivalent or stronger access to group (or admin privileges).

        Postconditions:

        2. User is made a member of the group at the chosen level.

        This may be repeated without harm to downgrade or upgrade members one has previously invited.

        :todo: not safe from removing last owner
        """
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        privilege_id = self.__get_privilege_id_from_code(privilege_code)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        requesting_id = self.__get_user_id_from_uuid(self.get_uuid())
        # sanity logic: no such thing as 'ns' access.
        # if privilege_code == 'ns':
        #     raise HSAccessException("privilege 'readable without sharing' does not apply to groups")
        # access control logic: cannot grant sharing above own privilege
        if not (self.user_is_admin(self.get_uuid())):
            # use join to access privilege records
            user_priv = self.__get_cumulative_user_privilege_over_group(group_uuid)
            if user_priv > self.__PRIVILEGE_RO:  # read-only or no-sharing
                raise HSAccessException("User has no privilege for group")
            if user_priv > privilege_id:
                raise HSAccessException("User has insufficient privilege for group")
        if user_uuid == self.get_uuid():
            if self.group_is_owned(group_uuid):
                if self.get_number_of_group_owners(group_uuid) == 1:
                    raise HSAccessException("Cannot remove last owner of group")

        self.__share_group_with_user(requesting_id, user_id, group_id, privilege_id)
        # for now, couple group membership with group privilege; the following is obsolete
        # self.assert_user_in_group(group_uuid, user_uuid)

    def __user_access_to_group_exists(self, requesting_id, user_id, group_id):
        """
        PRIVATE: Test whether there is an access record for a specific user, group, and asserting user

        :type requesting_id: int
        :type user_id: int
        :type group_id: int
        :param requesting_id: user id of user assigning privilege
        :param user_id: user id of user who needs privilege
        :param group_id: group id of group to which privilege will be assigned

        This is a helper routine for 'share_group_with_user'
        """
        self.__cur.execute(
            """select privilege_id from user_access_to_group where user_id=%s and group_id=%s
            and assertion_user_id=%s""",
            (user_id, group_id, requesting_id))
        if self.__cur.rowcount > 1:
            raise HSAIntegrityException("More than one record for a group privilege tuple")
        if self.__cur.rowcount > 0:
            return True
        else:
            return False

    def __share_group_with_user(self, requesting_id, user_id, group_id, privilege_id):
        """
        PRIVATE: unpoliced share of group with user

        :type requesting_id: int
        :type user_id: int
        :type group_id: int
        :param requesting_id: internal id of requesting user
        :param user_id: internal id of user to gain privilege
        :param group_id: internal id of group to which to grant privilege

        This is a helper routine for 'share_group_with_user'. It does not have access control.
        """
        if self.__user_access_to_group_exists(requesting_id, user_id, group_id):
            self.__share_group_user_update(requesting_id, user_id, group_id, privilege_id)
        else:
            self.__share_group_user_add(requesting_id, user_id, group_id, privilege_id)

    def __share_group_user_update(self, requesting_id, user_id, group_id, privilege_id):
        """
        PRIVATE: update user access to a group

        :type requesting_id: int
        :type user_id: int
        :type group_id: int
        :type privilege_id: int
        :param requesting_id: id of user requesting change
        :param user_id: id of user to be enabled
        :param group_id: id of group to be modified
        :param privilege_id: id of privilege to be installed

        This is a helper routine for 'share_group_with_user'. It does not have access control.
        There must already be a privilege record for the user, group, and current user.
        """
        self.__cur.execute("""update user_access_to_group set privilege_id = %s,
                              assertion_time=CURRENT_TIMESTAMP
                              where user_id=%s and group_id=%s and assertion_user_id=%s""",
                           (privilege_id, user_id, group_id, requesting_id))
        self.__conn.commit()

    def __share_group_user_add(self, requesting_id, user_id, group_id, privilege_id):
        """
        PRIVATE: add new user access for a group

        :type requesting_id: int
        :type user_id: int
        :type group_id: int
        :type privilege_id: int
        :param requesting_id: int: id of user requesting change
        :param user_id: int: id of user to be enabled
        :param group_id: int: id of group to be modified
        :param privilege_id: int: id of privilege to be installed

        This is a helper routine for 'share_group_with_user'. It does not have access control.
        There must not already be a privilege record for the user, group, and current user.
        """
        self.__cur.execute("""insert into user_access_to_group values (DEFAULT, %s, %s, %s, %s, DEFAULT)""",
                           (user_id, group_id, privilege_id, requesting_id))
        self.__conn.commit()

    # CLI: hs group remove ...
    def unshare_group_with_user(self, group_uuid, user_uuid=None):
        """
        Attempt to unshare a group with a user

        :type group_uuid: str
        :type user_uuid: str
        :param group_uuid: group identifier of group for which privilege should be removed.
        :param user_uuid: uuid of user for whom privilege should be removed; omit for current user.

        There are three conditions under which one can unshare a group with a user, either:

        1. user has admin, or

        2. user owns the group, or

        3. user is the user in question and wishes to leave the group

        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        # these serve as argument checks
        user_id = self.__get_user_id_from_uuid(user_uuid)
        group_id = self.__get_group_id_from_uuid(group_uuid)
        # requesting_id = self.__get_user_id_from_uuid(self.get_uuid())

        # access control logic:
        if self.user_is_admin(self.get_uuid()) \
                or self.group_is_owned(group_uuid) \
                or (user_uuid == self.get_uuid() and self.user_in_group(group_uuid, user_uuid)):
            if self.get_number_of_group_owners(group_uuid) > 1 or not self.group_is_owned(group_uuid, user_uuid):
                self.__cur.execute("delete from user_access_to_group where group_id=%s and user_id=%s",
                                   (group_id, user_id))
                self.__conn.commit()
            else:
                raise HSAccessException("Cannot remove last group owner, including self")
            # self.retract_user_from_group(user_uuid, group_uuid)
        else:
            raise HSAccessException("Regular user must own group")

    ###########################################################
    # faceted information retrieval
    ###########################################################
    # CLI: hs ls resources
    def get_resources_held_by_user(self, user_uuid=None):
        """
        Make a list of resources held by user, sorted by title

        :type user_uuid: str
        :param user_uuid: uuid of user; omit for current user.
        :return: List of resources containing dict items
        :rtype: list[dict[str, str]] 

        This returns a list of resource dict records, in the format::

            {
            'uuid': *uuid of resource*,
            'title': *title of resource*,
            'path': *path of resource*,
            'privilege': *privilege code*
            }

        Note: this is not currently subject to access control.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        self.__cur.execute("""select distinct r.resource_uuid, r.resource_title, r.resource_path, p.privilege_code
          from user_resource_privilege u
          left join resources r on r.resource_id = u.resource_id
          left join privileges p on p.privilege_id = u.privilege_id
          where user_id=%s order by r.resource_uuid""", (user_id,))
        result = []
        for row in self.__cur:
            result.append({'uuid': row['resource_uuid'],
                           'title': row['resource_title'],
                           'path': row['resource_path'],
                           'privilege': row['privilege_code']})
        return result

    def get_users_holding_resource(self, resource_uuid):
        """
        Make a list of resources held by user, sorted by title

        :type resource_uuid: str
        :param resource_uuid: uuid of user; omit for current user.
        :return: List of resources containing dict items
        :rtype: list[dict[str, str]] 

        This returns a list of user dict records, in the format::

            {
            'uuid': *uuid of user*,
            'name': *name of user*,
            'login': *login of user*,
            'privilege': *privilege code*
            }

        Note: this is not currently subject to access control.
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        self.__cur.execute("""select distinct u.user_uuid, u.user_name, u.user_login, p.privilege_code
          from user_resource_privilege urp
          left join users u on u.user_id = urp.user_id
          left join privileges p on p.privilege_id = urp.privilege_id
          where resource_id=%s order by u.user_name""", (resource_id,))
        result = []
        for row in self.__cur:
            result.append({'uuid': row['user_uuid'],
                           'name': row['user_name'],
                           'login': row['user_login'],
                           'privilege': row['privilege_code']})
        return result

    def get_resources_held_by_group(self, group_uuid):
        """
        Retrieve resources accessible to a specific group.

        :type group_uuid: str
        :param group_uuid: uuid of the group to check
        :return: List of Dicts of resource info
        :rtype: list[dict[str, str]] 

        This returns a list of resources accessible to a specific group, in the format::

            {
            'uuid': *uuid of resource*,
            'title': *title of resource*,
            'path': *path of resource*,
            'privilege': *privilege code*
            }

        Note: this is not subject to access control.
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        group_id = self.__get_group_id_from_uuid(group_uuid)
        self.__cur.execute("""select DISTINCT r.resource_title, r.resource_uuid, r.resource_path, q.privilege_code
                              from resources r
                              inner join group_resource_privilege p on r.resource_id = p.resource_id
                              left join privileges q on p.privilege_id = q.privilege_id
                              where p.group_id = %s""",
                           (group_id,))
        # map this into a dict structure
        result = []
        for row in self.__cur:
            result.append({'uuid': row['resource_uuid'],
                           'title': row['resource_title'],
                           'path': row['resource_path'],
                           'privilege': row['privilege_code']})
        return result

    def get_groups_holding_resource(self, resource_uuid):
        """
        Retrieve resources accessible to a specific group.

        :type resource_uuid: str
        :param resource_uuid: uuid of the resource to check
        :return: List of Dicts describing groups
        :rtype: list[dict[str, str]] 

        This returns a list of groups that can access a resource, in the format:

            {
            'uuid': *uuid of group*,
            'name': *name of group*,
            'privilege': *privilege code*
            }

        Note: this is not subject to access control.
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        self.__cur.execute("""select DISTINCT g.group_name, g.group_uuid, q.privilege_code
                              from group_resource_privilege p
                              LEFT JOIN groups g ON g.group_id = p.group_id
                              left join privileges q on p.privilege_id = q.privilege_id
                              where p.resource_id = %s""",
                           (resource_id,))
        # map this into a dict structure
        result = []
        for row in self.__cur:
            result.append({'uuid': row['group_uuid'],
                           'name': row['group_name'],
                           'privilege': row['privilege_code']})
        return result

    def get_public_resources(self):
        """
        Make a list of public resources, sorted by title

        :type user_uuid: str
        :param user_uuid: uuid of user; omit for current user.
        :return: List of resources containing dict items
        :rtype: list[dict[str, str]]

        This returns a list of resource dict records, in the format::

            {
            'uuid': *uuid of resource*,
            'title': *title of resource*,
            'path': *path of resource*,
            'privilege': *privilege code*
            }

        Note: this is not currently subject to access control.
        """
        self.__cur.execute("""select resource_uuid, resource_title, resource_path,
                           'ro' AS privilege_code
                           FROM resources
                           WHERE resource_public
                           ORDER BY resource_title""")
        result = []
        for row in self.__cur:
            result.append({'uuid': row['resource_uuid'],
                           'title': row['resource_title'],
                           'path': row['resource_path'],
                           'privilege': row['privilege_code']})
        return result

    def get_discoverable_resources(self):
        """
        Make a list of public resources, sorted by title

        :type user_uuid: str
        :param user_uuid: uuid of user; omit for current user.
        :return: List of resources containing dict items
        :rtype: list[dict[str, str]]

        This returns a list of resource dict records, in the format::

            {
            'uuid': *uuid of resource*,
            'title': *title of resource*,
            'path': *path of resource*,
            'privilege': *privilege code*
            }

        Note: this is not currently subject to access control.
        """
        self.__cur.execute("""select resource_uuid, resource_title, resource_path,
                           CASE WHEN resource_public THEN 'ro'
                                ELSE 'none'
                           END AS privilege_code
                           FROM resources
                           WHERE resource_discoverable is TRUE
                           ORDER BY resource_title""")
        result = []
        for row in self.__cur:
            result.append({'uuid': row['resource_uuid'],
                           'title': row['resource_title'],
                           'path': row['resource_path'],
                           'privilege': row['privilege_code']})
        return result

    # CLI: hs ls groups
    def groups_of_user(self, user_uuid=None):
        """
        Make a list of groups in which a user is a member.

        :type user_uuid: str
        :param user_uuid: uuid of user, or None to use current authorized user
        :return: List of Dict entries for groups of user. 
        :rtype: list[dict[str, str]] 

        This returns a list of dictionaries, each of the form::

            {
            'uuid': *group's uuid*,
            'name': *group's name*
            }

        for use in displaying group data.

        """
        # default to irods user if no uuid given
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        self.__cur.execute("""select distinct g.group_uuid, g.group_name
                              from user_membership_in_group m left join groups g on m.group_id=g.group_id
                              where user_id=%s order by g.group_name, g.group_uuid""",
                           (user_id,))
        result = []
        for row in self.__cur:
            result.append({'uuid': row['group_uuid'], 'name': row['group_name']})
        return result

    # ##########################################################
    # stubs for folder subsystem
    # ##########################################################
    def assert_folder(self, folder_name):
        """
        STUB: Create a folder in the user_folders relation

        :type folder_name: str
        :param folder_name: The name of the folder

        Uses self.get_uuid(): the identity of the current user.
        Folders are local to the current user.
        """
        return

    def retract_folder(self, folder_name):
        """
        STUB: Remove a folder; things in the folder become "unfiled"

        :type folder_name: str
        :param folder_name: The name of the folder

        Uses: self.get_uuid(): the identity of the current user.
        Folders are local to the current user.
        """
        return

    def assert_resource_in_folder(self, resource_uuid, folder_name):
        """
        STUB: Put a resource into a previously created folder

        :type resource_uuid: str
        :type folder_name: str
        :param resource_uuid: identifier of resource to put into folder
        :param folder_name: name of the folder

        Uses self.get_uuid(): the identity of the current user.
        Folders are local to the current user.
        """
        return

    def retract_resource_in_folder(self, resource_uuid, folder_name):
        """
        STUB: Remove a resource from a folder; it becomes unfiled.

        :type resource_uuid: str
        :type folder_name: str
        :param resource_uuid: identifier of resource to put into folder
        :param folder_name: name of the folder
        """
        return

    def get_folders(self):
        """
        STUB: Return a list of folders for this user

        :return: A list of folder names
        :rtype: List<str> 

        Uses self.get_uuid(): current user identity
        """
        return

    def get_resources_in_folders(self, folder=None):
        """
        STUB: Get a structured dictionary of folders and their contents

        :type folder: str
        :param folder: the optional name of a folder to use as the top of the hierarchy
        :return: A dict object of contents
        :rtype: Dict<str> 

        Uses self.get_uuid(): the current user.

        This returns a dictionary structure of the form::

            { folder: { resource_uuid : { title : *resource title*, 'access' : *access code* }}}

        1. If folder is None, report on the whole hierarchy of user folders

        2.  If folder is not None, report on only one chosen folder.

        """
        return

    # ##########################################################
    # stubs for tag subsystem
    # ##########################################################
    def assert_tag(self, tag_name):
        """
        STUB: Create a tag in the user_tags relation

        :type tag_name: str
        :param tag_name: The name of the tag

        Uses self.get_uuid(): the identity of the current user.

        Registers a tag for later uses. This assures that tags are unambiguous when applied.
        Folders are local to the current user.
        """
        return

    def retract_tag(self, tag_name):
        """
        STUB: Remove a tag; things in the tag become "untagged"

        :type tag_name: str
        :param tag_name: The name of the tag

        Uses self.get_uuid(): the identity of the current user.

        Unregisters a tag along with all of uses of that tag on resources.
        Folders are local to the current user.
        """
        return

    def assert_resource_has_tag(self, resource_uuid, tag_name):
        """
        STUB: Assign a resource a previously created tag

        :type resource_uuid: str
        :type tag_name: str
        :param resource_uuid: identifier of resource to put into tag
        :param tag_name: name of the tag

        Uses self.get_uuid(): the identity of the current user.
        Tags are local to the current user.
        Multiple asserts with different tags apply all of them
        """
        return

    def retract_resource_has_tag(self, resource_uuid, tag_name):
        """
        STUB: Remove a tag from a resource; it becomes untagged.

        :type resource_uuid: str
        :type tag_name: str
        :param resource_uuid: identifier of resource to put into tag
        :param tag_name: name of the tag

        Uses self.get_uuid(): the identity of the current user.
        Tags are local to the current user.
        This removes an assertion of one tag while leaving the others alone.
        """
        return

    def get_tags(self):
        """
        STUB: Return a list of tags for this user

        :return: A list of tag names
        :rtype: List<str> 

        Uses self.get_uuid(): current user identity
        """
        return

    def get_resources_by_tag(self, tag=None):
        """
        STUB: Get a structured dictionary of tags and their contents

        :type tag: str
        :param tag: the name of a tag to use
        :return: A dict object of contents
        :rtype: Dict<str> 

        Uses: self.get_uuid(): the current user.
        This returns a dictionary structure of the form::

            { "tag": { resource_uuid : { title : *resource title*, 'access' : *access code* }}}

        If tag argument is not None, report on only one tag.
        """
        return

    ####################################################################
    # statistics
    ####################################################################

    def get_number_of_resource_owners(self, resource_uuid):
        """
        Count the number of resource owners for a resource, for reporting purposes.

        :type resource_uuid: str
        :param resource_uuid: identifier of resource to report upon
        :return: number of owners
        :rtype: int
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        resource_id = self.__get_resource_id_from_uuid(resource_uuid)
        return self.__get_number_of_resource_owners_by_id(resource_id)

    def __get_number_of_resource_owners_by_id(self, resource_id):
        self.__cur.execute("""select count(distinct user_id) as count from user_resource_privilege
                              where resource_id=%s and privilege_id=1""",
                           (resource_id,))
        return self.__cur.fetchone()['count']

    def get_number_of_group_owners(self, group_uuid):
        """
        Count the number of resource owners for a resource, for reporting purposes.

        :type group_uuid: str
        :param group_uuid: identifier of group to report upon
        :return: number of owners
        :rtype: int
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        group_id = self.__get_group_id_from_uuid(group_uuid)
        return self.__get_number_of_group_owners_by_id(group_id)

    def __get_number_of_group_owners_by_id(self, group_id):
        self.__cur.execute("""select count(distinct user_id) as count from user_group_privilege
                              where group_id=%s and privilege_id=1""",
                           (group_id,))
        return self.__cur.fetchone()['count']

    def get_number_of_resources_owned_by_user(self, user_uuid=None):
        """
        Count the number of resources owned by a user.

        :type user_uuid: str
        :param user_uuid: identifier of group to report upon; None reports upon current user
        :return: number of resources owned
        :rtype: int

        Note: this reports on any user independent of the privilege of the current user.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        self.__cur.execute("""select count(distinct resource_id) as count from user_resource_privilege
                              where user_id=%s and privilege_id=1""",
                           (user_id,))
        return self.__cur.fetchone()['count']

    # get the number of groups the user owns
    def get_number_of_groups_owned_by_user(self, user_uuid=None):
        """
        Count the number of groups owned by a user.

        :type user_uuid: str
        :param user_uuid: identifier of group to report upon; None reports upon current user
        :return: number of groups owned
        :rtype: int

        Note: this reports on any user independent of the privilege of the current user.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        self.__cur.execute("""select count(distinct group_id) as count from user_group_privilege
                              where user_id=%s and privilege_id=1""",
                           (user_id,))
        return self.__cur.fetchone()['count']

    # measure the number of resources the user can access
    def get_number_of_resources_held_by_user(self, user_uuid=None):
        """
        Count the number of resources held by a user.

        :type user_uuid: str
        :param user_uuid: identifier of group to report upon; None reports upon current user
        :return: number of resources held
        :rtype: int

        Note: this reports on any user independent of the privilege of the current user.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        self.__cur.execute("""select count(distinct resource_id) as count from user_resource_privilege
                              where user_id=%s""",
                           (user_id,))
        return self.__cur.fetchone()['count']

    # measure the number of resources the user can access
    # note: group membership and access are currently synonymous
    # I am utilizing group access as the count.

    def get_number_of_groups_of_user(self, user_uuid=None):
        """
        Count the number of groups in which a user is a member

        :type user_uuid: str
        :param user_uuid: identifier of group to report upon; None reports upon current user
        :return: number of groups joined
        :rtype: int

        Note: this reports on any user independent of the privilege of the current user.
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        if not self.user_exists(user_uuid):
            raise HSAUsageException("User uuid does not exist")
        user_id = self.__get_user_id_from_uuid(user_uuid)
        self.__cur.execute("""select count(distinct group_id) as count from user_group_privilege
                              where user_id=%s""",
                           (user_id,))
        return self.__cur.fetchone()['count']

    ##################################################################################
    # quick utility routines for obtaining current user information
    ##################################################################################

    def get_uuid(self):
        """
        Returns the uuid of the current user

        :return: uuid of current user
        :rtype: str
        """
        return self.__user_uuid

    def get_login(self):
        """
        Returns the (iRODS) login name of the current user

        :return: login name of current user
        :rtype: str
        """
        return self.__irods_user

    #################################################
    # reset everything for testing
    #################################################

    def __global_reset(self, are_you_sure):
        """
        PRIVATE: Delete all data from the database except for starting situation, for testing.

        :type are_you_sure: str
        :param are_you_sure: a string that must have the value "yes, I'm sure"

        This clears the database to an install state. This is used for testing,
        and never in production.
        """
        if self.user_is_admin():
            if are_you_sure == "yes, I'm sure":
                self.__cur.execute("delete from user_tags_of_resource")
                self.__cur.execute("delete from user_folder_of_resource")
                self.__cur.execute("delete from group_access_to_resource")
                # self.__cur.execute("delete from user_membership_in_group")
                self.__cur.execute("delete from user_invitations_to_resource")
                self.__cur.execute("delete from user_invitations_to_group")
                self.__cur.execute("delete from user_access_to_group")
                self.__cur.execute("delete from user_access_to_resource")
                self.__cur.execute("delete from user_folders")
                self.__cur.execute("delete from user_tags")
                self.__cur.execute("delete from groups")
                self.__cur.execute("delete from resources")
                self.__cur.execute("delete from users where user_id != 1")
                self.__conn.commit()
        else:
            raise HSAccessException("User is not an administrator")


# class encapsulates all access control actions, including convenience functions
class HSAccess(HSAccessCore):
    """
    Access control class for HydroShare Users, Resources, and Groups
    """
    def __init__(self, irods_user, irods_password,
                 db_database, db_user, db_password, db_host, db_port):
        HSAccessCore.__init__(self, irods_user, irods_password,
                              db_database, db_user, db_password, db_host, db_port)

    def __del__(self):
        HSAccessCore.__del__(self)

    ###########################################################
    # convenience functions for user state (administrators only)
    ###########################################################

    def make_user_active(self, user_uuid):
        meta = self.get_user_metadata(user_uuid)
        if not meta['active']:
            meta['active'] = True
            self.assert_user_metadata(meta)

    def make_user_not_active(self, user_uuid):
        meta = self.get_user_metadata(user_uuid)
        if meta['active']:
            meta['active'] = False
            self.assert_user_metadata(meta)

    def make_user_admin(self, user_uuid):
        meta = self.get_user_metadata(user_uuid)
        if not meta['admin']:
            meta['admin'] = True
            self.assert_user_metadata(meta)

    def make_user_not_admin(self, user_uuid):
        meta = self.get_user_metadata(user_uuid)
        if meta['admin']:
            meta['admin'] = False
            self.assert_user_metadata(meta)

    ###########################################################
    # Convenience functions for resource state
    ###########################################################

    # there is no 'make_resource_mutable' for normal users: this is discouraged!
    def make_resource_immutable(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if not meta['immutable']:
            meta['immutable'] = True
            self.assert_resource_metadata(meta, user_uuid)

    # admin only
    def make_resource_not_immutable(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if not meta['immutable']:
            meta['immutable'] = False
            self.assert_resource_metadata(meta, user_uuid)

    # making a resource public -- as a side effect -- makes it discoverable
    def make_resource_public(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if not meta['public']:  # or not meta['discoverable']:
            meta['public'] = True
            # meta['discoverable'] = True  # should I do this?
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    def make_resource_not_public(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if meta['public']:
            meta['public'] = False
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    def make_resource_discoverable(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if not meta['discoverable']:
            meta['discoverable'] = True
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    def make_resource_not_discoverable(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if meta['discoverable']:
            meta['discoverable'] = False
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    def make_resource_published(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if not meta['published']:  # or not meta['discoverable']:
            meta['published'] = True
            # meta['discoverable'] = True  # should I do this?
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    def make_resource_not_published(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if meta['published']:
            meta['published'] = False
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    def make_resource_shareable(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if not meta['shareable']:
            meta['shareable'] = True
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    def make_resource_not_shareable(self, resource_uuid, user_uuid=None):
        meta = self.get_resource_metadata(resource_uuid)
        if meta['shareable']:
            meta['shareable'] = False
            # this checks access privileges
            self.assert_resource_metadata(meta, user_uuid)

    ###########################################################
    # Convenience functions for group state
    ###########################################################
    def make_group_active(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if not meta['active']:
            meta['active'] = True
            self.assert_group_metadata(meta)

    def make_group_not_active(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if meta['active']:
            meta['active'] = False
            self.assert_group_metadata(meta)

    def make_group_shareable(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if not meta['shareable']:
            meta['shareable'] = True
            self.assert_group_metadata(meta)

    def make_group_not_shareable(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if meta['shareable']:
            meta['shareable'] = False
            self.assert_group_metadata(meta)

    def make_group_public(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if not meta['public']:
            meta['public'] = True
            self.assert_group_metadata(meta)

    def make_group_not_public(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if meta['public']:
            meta['public'] = False
            self.assert_group_metadata(meta)

    def make_group_discoverable(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if not meta['discoverable']:
            meta['discoverable'] = True
            self.assert_group_metadata(meta)

    def make_group_not_discoverable(self, group_uuid):
        meta = self.get_group_metadata(group_uuid)
        if meta['discoverable']:
            meta['discoverable'] = False
            self.assert_group_metadata(meta)

    ###########################################################
    # print names for users, resources, and groups
    ###########################################################
    def get_user_print_name(self, user_uuid=None):
        """
        Constructs a print name for any given user

        :type user_uuid: str
        :param user_uuid: identifier of user, None for current user
        :return: print name for requested user
        :rtype: str
        """
        if user_uuid is None:
            user_uuid = self.get_uuid()
        if not (type(user_uuid) is unicode or type(user_uuid) is str):
            raise HSAUsageException("user_uuid is not a unicode or str")
        meta = self.get_user_metadata(user_uuid)
        return meta['name'] + '(' + meta['uuid'] + ')'

    def get_resource_print_name(self, resource_uuid):
        """
        Constructs a print name for any given resource

        :type resource_uuid: str
        :param resource_uuid: identifier of resource
        :return: print name for requested resource
        :rtype: str
        """
        if not (type(resource_uuid) is unicode or type(resource_uuid) is str):
            raise HSAUsageException("resource_uuid is not a unicode or str")

        meta = self.get_resource_metadata(resource_uuid)
        return meta['title'] + '(' + meta['uuid'] + ')'

    def get_group_print_name(self, group_uuid):
        """
        Constructs a print name for any given group

        :type group_uuid: str
        :param group_uuid: identifier of group
        :return: print name for requested group
        :rtype: str
        """
        if not (type(group_uuid) is unicode or type(group_uuid) is str):
            raise HSAUsageException("group_uuid is not a unicode or str")
        meta = self.get_group_metadata(group_uuid)
        return meta['name'] + '(' + meta['uuid'] + ')'
