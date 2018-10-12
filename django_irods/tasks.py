"""
The following is a list of the IRODS celery tasks and a brief description of
what each does:

* iadmin   - perform irods administrator operations (irods admins only).
* ibun     - upload/download structured (tar) files.
* ichksum  - checksum one or more data-objects or collections.
* ichmod   - change access permissions to collections or data-objects.
* icp      - copy a data-object (file) or collection (directory) to another.
* iexecmd  - remotely execute special commands.
* ifsck    - check if local files/directories are consistent with the associated objects/collections in iRODS.
* iget     - get a file from iRODS.
* ilocate  - search for data-object(s) OR collections (via a script).
* ils      - list collections (directories) and data-objects (files).
* ilsresc  - list iRODS resources and resource-groups.
* imcoll   - manage mounted collections and associated cache.
* imeta    - add/remove/copy/list/query user-defined metadata.
* imiscsvrinfo - retrieve basic server information.
* imkdir   - make an irods directory (collection).
* imv      - move/rename an irods data-object (file) or collection (directory).
* ipasswd  - change your irods password.
* iphybun  - physically bundle files (admin only).
* iphymv   - physically move a data-object to another storage resource.
* ips      - display iRODS agent (server) connection information.
* iput     - put (store) a file into iRODS.
* iqdel    - remove a delayed rule (owned by you) from the queue.
* iqmod    - modify certain values in existing delayed rules (owned by you).
* iqstat   - show the queue status of delayed rules.
* iquest   - issue a question (query on system/user-defined metadata).
* iquota   - show information on iRODS quotas (if any).
* ireg     - register a file or directory/files/subdirectories into iRODS.
* irepl    - replicate a file in iRODS to another storage resource.
* irm      - remove one or more data-objects or collections.
* irmtrash - remove data-objects from the trash bin.
* irsync   - synchronize collections between a local/irods or irods/irods.
* irule    - submit a rule to be executed by the iRODS server.
* iscan    - check if local file or directory is registered in irods.
* isysmeta - show or modify system metadata.
* itrim    - trim down the number of replicas of data-objects.
* iuserinfo- show information about your iRODS user account.
* ixmsg    - send/receive iRODS xMessage System messages.
"""

from celery.task import Task
from celery.task.sets import subtask
from icommands import Session, GLOBAL_SESSION, IRodsEnv

from . import models as m
from uuid import uuid4
import os
import tempfile
import requests
from django.conf import settings

class RodsException(Exception):
    pass


class IRODSTask(Task):
    abstract=True

    def __init__(self, *args, **kwargs):
        super(IRODSTask, self).__init__(*args, **kwargs)
        self._sessions = {}
        self._mounted_collections = {}
        self._mounted_names = {}

    def session(self, environment=None):
        if getattr(settings, 'IRODS_GLOBAL_SESSION', False):
            return GLOBAL_SESSION

        if environment is None:
            environment = IRodsEnv(
                pk=-1,
                host=settings.IRODS_HOST,
                port=settings.IRODS_PORT,
                def_res=settings.IRODS_DEFAULT_RESOURCE,
                home_coll=settings.IRODS_HOME_COLLECTION,
                cwd=settings.IRODS_CWD,
                username=settings.IRODS_USERNAME,
                zone=settings.IRODS_ZONE,
                auth=settings.IRODS_AUTH,
                irods_default_hash_scheme='MD5'
            )
        elif isinstance(environment, int):
            environment = m.RodsEnvironment.objects.get(pk=environment)

        if environment.pk not in self._sessions:
            session = Session("/tmp/django_irods", settings.IRODS_ICOMMANDS_PATH, session_id=uuid4())
            session.create_environment(environment)
            session.run('iinit', None, environment.auth)

            self._sessions[environment.pk] = session

        return self._sessions[environment.pk]

    def mount(self, environment, local_name, collection=None):
        if local_name not in self._mounted_collections:
            if collection:
                self.session(environment).run('icd', None, collection)

            path = os.path.join(self.session(environment).session_path, local_name)
            os.mkdir(path)
            self.session(environment).run('irodsFs', None, path)
            self._mounted_collections[local_name] = collection
            self._mounted_names[local_name] = path
        return self._mounted_names[local_name]

    def collection(self, name):
        return self._mounted_names[name]

    def unmount(self, local_name):
        if not hasattr(self, '_mounted_collections'):
            return None

        if local_name in self._mounted_collections:
            os.system("fusermount -uz {local_name}".format(local_name=self.collection(local_name)))

    def __del__(self):
        for name in self._mounted_names.keys():
            self.unmount(name)
        for session in self._sessions.values():
            session.run('iexit')
            session.delete_environment()

    def run(self, environment, *options, **kwargs):
        return self.session(environment).run(self.name, None, *options)

CHUNK_SIZE=8192

class IGet(IRODSTask):
    name = 'django_irods.tasks.iget'

    def run(self, environment, path, callback=None, post=None, post_name=None, *options):
        """
        Usage: iget [-fIKPQrUvVT] [-n replNumber] [-N numThreads] [-X restartFile]
        [-R resource] srcDataObj|srcCollection ... destLocalFile|destLocalDir

        Usage : iget [-fIKPQUvVT] [-n replNumber] [-N numThreads] [-X restartFile]
        [-R resource] srcDataObj|srcCollection

        Usage : iget [-fIKPQUvVT] [-n replNumber] [-N numThreads] [-X restartFile]
        [-R resource] srcDataObj ... -

        Get data-objects or collections from irods space, either to the specified
        local area or to the current working directory.

        If the destLocalFile is '-', the files read from the server will be
        written to the standard output (stdout). Similar to the UNIX 'cat'
        command, multiple source files can be specified.

        The -X option specifies that the restart option is on and the restartFile
        input specifies a local file that contains the restart info. If the
        restartFile does not exist, it will be created and used for recording
        subsequent restart info. If it exists and is not empty, the restart info
        contained in this file will be used for restarting the operation.
        Note that the restart operation only works for uploading directories and
        the path input must be identical to the one that generated the restart file

        The -Q option specifies the use of the RBUDP transfer mechanism which uses
        the UDP protocol for data transfer. The UDP protocol is very efficient
        if the network is very robust with few packet losses. Two environment
        variables - rbudpSendRate and rbudpPackSize are used to tune the RBUDP
        data transfer. rbudpSendRate is used to throttle the send rate in
        kbits/sec. The default rbudpSendRate is 600,000. rbudpPackSize is used
        to set the packet size. The dafault rbudpPackSize is 8192. The -V option
        can be used to show the loss rate of the transfer. If the lost rate is
        more than a few %, the sendrate should be reduced.

        The -T option will renew the socket connection between the client and
        server after 10 minutes of connection. This gets around the problem of
        sockets getting timed out by the firewall as reported by some users.

        Options are:
        * -f  force - write local files even it they exist already (overwrite them)
        * -I  redirect connection - redirect the connection to connect directly
               to the best (determiined by the first 10 data objects in the input
               collection) resource server.
        * -K  verify the checksum
        * -n  replNumber - retrieve the copy with the specified replica number
        * -N  numThreads - the number of thread to use for the transfer. A value of
               0 means no threading. By default (-N option not used) the server
               decides the number of threads to use.
        * -P  output the progress of the download.
        * -r  recursive - retrieve subcollections
        * -R  resource - the preferred resource
        * -T  renew socket connection after 10 minutes
        * -Q  use RBUDP (datagram) protocol for the data transfer
        * -v  verbose
        * -V  Very verbose
             restartFile input specifies a local file that contains the restart info.
        * -X  restartFile - specifies that the restart option is on and the
             restartFile input specifies a local file that contains the restart info.
        * -h  this help

        :param environment: a dict or primary key of the RodsEnvironment model that governs this session
        :param path: the path to get from
        :param callback: a registered Celery task that can be called as a subtask with the entire contents of the file that was gotten (file must fit in memory)
        :param post: a URL to which the results of the iget can be POSTed.  File can be larger than available memory.
        :param post_name: the filename that the POST will be given.
        :param options: any of the above command line options.
        :return:
        """

        options += ('-',) # we're redirecting to stdout.

        proc = self.session(environment).run_safe('iget', None, path, *options)
        tmp = tempfile.SpooledTemporaryFile()   # spool to disk if the iget is too large
        chunk = proc.stdout.read(CHUNK_SIZE)
        while chunk:
            tmp.write(chunk)
            chunk = proc.stdout.read(CHUNK_SIZE)

        tmp.flush()
        tmp.seek(0)

        if callback:
            data = tmp.read()
            subtask(callback).delay(data)
            return None
        elif post:
            rsp =  requests.post(post, files={post_name: tmp})
            return {
                'code' : rsp.status_code,
                'content' : rsp.content
            }
        else:
            return tmp.read()

class IPut(IRODSTask):
    name = 'django_irods.tasks.iput'

    def run(self, environment, data_is_file, path, data, *options):
        """
        Usage : iput [-abfIkKPQrTUvV] [-D dataType] [-N numThreads] [-n replNum]
                 [-p physicalPath] [-R resource] [-X restartFile] [--link]
            localSrcFile|localSrcDir ...  destDataObj|destColl
        Usage : iput [-abfIkKPQTUvV] [-D dataType] [-N numThreads] [-n replNum]
                     [-p physicalPath] [-R resource] [-X restartFile] [--link]
                       localSrcFile

        Store a file into iRODS.  If the destination data-object or collection are
        not provided, the current irods directory and the input file name are used.
        The -X option specifies that the restart option is on and the restartFile
        input specifies a local file that contains the restart info. If the
        restartFile does not exist, it will be created and used for recording
        subsequent restart info. If it exists and is not empty, the restart info
        contained in this file will be used for restarting the operation.
        Note that the restart operation only works for uploading directories and
        the path input must be identical to the one that generated the restart file

        If the options -f is used to overwrite an existing data-object, the copy
        in the resource specified by the -R option will be picked if it exists.
        Otherwise, one of the copy in the other resources will be picked for the
        overwrite. Note that a copy will not be made in the specified resource
        if a copy in the specified resource does not already exist. The irepl
        command should be used to make a replica of an existing copy.

        The -I option specifies the redirection of the connection so that it can
        be connected directly to the resource server. This option can improve
        the performance of uploading a large number of small (<32 Mbytes) files.
        This option is only effective if the source is a directory and the -f
        option is not used

        The -Q option specifies the use of the RBUDP transfer mechanism which uses
        the UDP protocol for data transfer. The UDP protocol is very efficient
        if the network is very robust with few packet losses. Two environment
        variables - rbudpSendRate and rbudpPackSize are used to tune the RBUDP
        data transfer. rbudpSendRate is used to throttle the send rate in
        kbits/sec. The default rbudpSendRate is 600,000. rbudpPackSize is used
        to set the packet size. The dafault rbudpPackSize is 8192. The -V option
        can be used to show the loss rate of the transfer. If the lost rate is
        more than a few %, the sendrate should be reduced.

        The -T option will renew the socket connection between the client and
        server after 10 minutes of connection. This gets around the problem of
        sockets getting timed out by the firewall as reported by some users.

        The -b option specifies bulk upload operation which can do up to 50 uploads
        at a time to reduce overhead. If the -b is specified with the -f option
        to overwrite existing files, the operation will work only if there is no
        existing copy at all or if there is an existing copy in the target resource.
        The operation will fail if there are existing copies but not in the
        target resource because this type of operation requires a replication
        operation and bulk replication has not been implemented yet.
        The bulk option does work for mounted collections which may represent the
        quickest way to upload a large number of small files.

        Options are:
        * -a  all - update all existing copy
        * -b  bulk upload to reduce overhead
        * -D  dataType - the data type string
        * -f  force - write data-object even it exists already; overwrite it
        * -I  redirect connection - redirect the connection to connect directly
               to the resource server.
        * -k  checksum - calculate a checksum on the data
        * -K  verify checksum - calculate and verify the checksum on the data
        * --link - ignore symlink.
        * -N  numThreads - the number of thread to use for the transfer. A value of
               0 means no threading. By default (-N option not used) the server
               decides the number of threads to use.
        * -p physicalPath - the physical path of the uploaded file on the sever
        * -P  output the progress of the upload.
        * -Q  use RBUDP (datagram) protocol for the data transfer
        * -R  resource - specifies the resource to store to. This can also be specified
             in your environment or via a rule set up by the administrator.
        * -r  recursive - store the whole subdirectory
        * -T  renew socket connection after 10 minutes
        * -v  verbose
        * -V  Very verbose
        * -X  restartFile - specifies that the restart option is on and the
             restartFile input specifies a local file that contains the restart info.
        * -h  this help

        :param environment: a dict or primary key of the RodsEnvironment model that governs this session
        :param path: the path to store the object in
        :param data: the data object to store
        :param options: any of the above command line options.
        :return: stdout, stderr of the command.
        """
        if not data_is_file:
            with tempfile.NamedTemporaryFile('w+b') as tmp:
                tmp.write(data)
                tmp.flush()
                tmp.seek(0)

                options += (tmp.name, path)
                return self.session(environment).run('iput', None, *options)
        else:
            options += (data, path)
            return self.session(environment).run('iput', None, *options)


class ILs(IRODSTask):
    """
    Display data Objects and collections stored in irods. Options are:
        * -A  ACL (access control list) and inheritance format
        * -l  long format
        * -L  very long format
        * -r  recursive - show subcollections
        * -v  verbose
        * -V  Very verbose
        * -h  this help

    :param environment: a dict or primary key of the RodsEnvironment model that governs this session
    :param options: any of the above command line options
    :return: stdout, stderr tuple of the command.
    """
    name = 'django_irods.tasks.ils'

class IAdmin(IRODSTask):
    """
    Usage: iadmin [-hvV] [command]

    A blank execute line invokes the interactive mode, where it
    prompts and executes commands until 'quit' or 'q' is entered.
    Single or double quotes can be used to enter items with blanks.

    Commands are:
    * lu [name[#Zone]] (list user info; details if name entered)
    * lua [name[#Zone]] (list user authentication (GSI/Kerberos Names, if any))
    * luan Name (list users associated with auth name (GSI/Kerberos)
    * lt [name] [subname] (list token info)
    * lr [name] (list resource info)
    * ls [name] (list directory: subdirs and files)
    * lz [name] (list zone info)
    * lg [name] (list group info (user member list))
    * lgd name  (list group details)
    * lrg [name] (list resource group info)
    * lf DataId (list file details; DataId is the number (from ls))
    * mkuser Name[#Zone] Type (make user)
    * moduser Name[#Zone] [ type | zone | comment | info | password ] newValue
    * aua Name[#Zone] Auth-Name (add user authentication-name (GSI/Kerberos)
    * rua Name[#Zone] Auth-Name (remove user authentication name (GSI/Kerberos)
    * rmuser Name[#Zone] (remove user, where userName: name[@department][#zone])
    * mkdir Name [username] (make directory(collection))
    * rmdir Name (remove directory)
    * mkresc Name Type Class Host [Path] (make Resource)
    * modresc Name [name, type, class, host, path, status, comment, info, freespace] Value (mod Resc)
    * rmresc Name (remove resource)
    * mkzone Name Type(remote) [Connection-info] [Comment] (make zone)
    * modzone Name [ name | conn | comment ] newValue  (modify zone)
    * rmzone Name (remove zone)
    * mkgroup Name (make group)
    * rmgroup Name (remove group)
    * atg groupName userName[#Zone] (add to group - add a user to a group)
    * rfg groupName userName[#Zone] (remove from group - remove a user from a group)
    * atrg resourceGroupName resourceName (add (resource) to resource group)
    * rfrg resourceGroupName resourceName (remove (resource) from resource group)
    * at tokenNamespace Name [Value1] [Value2] [Value3] (add token)
    * rt tokenNamespace Name [Value1] (remove token)
    * spass Password Key (print a scrambled form of a password for DB)
    * dspass Password Key (descramble a password and print it)
    * pv [date-time] [repeat-time(minutes)] (initiate a periodic rule to vacuum the DB)
    * ctime Time (convert an iRODS time (integer) to local time; & other forms)
    * suq User ResourceName-or-'total' Value (set user quota)
    * sgq Group ResourceName-or-'total' Value (set group quota)
    * lq [Name] List Quotas
    * cu (calulate usage (for quotas))
    * rum (remove unused metadata (user-defined AVUs)
    * asq 'SQL query' [Alias] (add specific query)
    * rsq 'SQL query' or Alias (remove specific query)
    * help (or h) [command] (this help, or more details on a command)
    Also see 'irmtrash -M -u user' for the admin mode of removing trash and
    similar admin modes in irepl, iphymv, and itrim.
    The admin can also alias as any user via the 'clientUserName' environment
    variable.

    :param environment:
    :param options:
    :return:
    """
    name = 'django_irods.tasks.iadmin'
    def run(self, environment, command, *options):
        return self.session(environment).run('iadmin', None, command, *options)

class IBundle(IRODSTask):

   """
   Usage : ibun -x [-hb] [-R resource] structFilePath
               irodsCollection

   Usage : ibun -c [-hf] [-R resource] [-D dataType] structFilePath
               irodsCollection

   Bundle file operations. This command allows structured files such as
   tar files to be uploaded and downloaded to/from iRODS.

   A tar file containing many small files can be created with normal unix
   tar command on the client and then uploaded to the iRODS server as a
   normal iRODS file. The 'ibun -x' command can then be used to extract/untar
   the uploaded tar file. The extracted subfiles and subdirectories will
   appeared as normal iRODS files and sub-collections. The 'ibun -c' command
   can be used to tar/bundle an iRODS collection into a tar file.

   For example, to upload a directory mydir to iRODS::

       tar -chlf mydir.tar -C /x/y/z/mydir .
       iput -Dtar mydir.tar .
       ibun -x mydir.tar mydir

   Note the use of -C option with the tar command which will tar the
   content of mydir but without including the directory mydir in the paths.
   The 'ibun -x' command extracts the tar file into the mydir collection.
   The target mydir collection does not have to exist nor be empty.
   If a subfile already exists in the target collection, the ingestion
   of this subfile will fail (unless the -f flag is set) but the process
   will continue.

   It is generally a good practice to tag the tar file using the -Dtar flag
   when uploading the file using iput. But if the tag is not made,
   the server assumes it is a tar dataType. The dataType tag can be added
   afterward with the isysmeta command. For example:
   isysmeta mod /tempZone/home/rods/mydir.tar datatype 'tar file'

   The following command bundles the iRods collection mydir into a tar file::

        ibun -cDtar mydir1.tar mydir

   If a copy of a file to be bundled does not exist on the target resource,
   a replica will automatically be made on the target resource.
   Again, if the -D flag is not use, the bundling will be done using tar.

   The -b option when used with the -x option, specifies bulk registration
   which does up to 50 rgistrations at a time to reduce overhead.

   Options are:
   * -b  bulk registration when used with -x to reduce overhead
   * -R  resource - specifies the resource to store to. This is optional
     in your environment
   * -D  dataType - the struct file data type. Valid only if the struct file
     does not exist. Currently only one dataType - 't' which specifies
     a tar file type is supported. If -D is not specified, the default is
     a tar file type
   * -x  extract the structFile and register the extracted files and directories
     under the input irodsCollection
   * -c  bundle the files and sub-collection underneath the input irodsCollection
     and store it in the structFilePath
   * -f  force overwrite the struct file (-c) or the subfiles (-x).
   * -h  this help

   :param environment:
   :param options:
   :return:
   """
   def run(self, environment, command, *options):
       return self.session(environment).run('iadmin', None, command, *options)


class IChksum(IRODSTask):
    name = 'django_irods.tasks.ichksum'


class Ichmod(IRODSTask):
    name = 'django_irods.tasks.ichmod'


class Icp(IRODSTask):
    name = 'django_irods.tasks.icp'


class Iexecmd(IRODSTask):
    name = 'django_irods.tasks.iexecmd'


class Ifsck(IRODSTask):
    name = 'django_irods.tasks.ifsck'


class Ilocate(IRODSTask):
    name = 'django_irods.tasks.ilocate'


class Ilsresc(IRODSTask):
    name = 'django_irods.tasks.ilsresc'


class Imcoll(IRODSTask):
    name = 'django_irods.tasks.imcoll'


class Imeta(IRODSTask):
    name = 'django_irods.tasks.imeta'


class Imiscserverinfo(IRODSTask):
    name = 'django_irods.tasks.imiscserverinfo'


class Imkdir(IRODSTask):
    name = 'django_irods.tasks.imkdir'


class Imv(IRODSTask):
    name = 'django_irods.tasks.imv'


class Iphybun(IRODSTask):
    name = 'django_irods.tasks.iphybun'


class Iphymv(IRODSTask):
    name = 'django_irods.tasks.iphymv'


class Ips(IRODSTask):
    name = 'django_irods.tasks.ips'


class Iqdel(IRODSTask):
    name = 'django_irods.tasks.iqdel'


class Iqmod(IRODSTask):
    name = 'django_irods.tasks.iqmod'


class Iqstat(IRODSTask):
    name = 'django_irods.tasks.iqstat'


class Iquest(IRODSTask):
    name = 'django_irods.tasks.iquest'


class Iquota(IRODSTask):
    name = 'django_irods.tasks.iquota'


class Ireg(IRODSTask):
    name = 'django_irods.tasks.ireg'


class Irepl(IRODSTask):
    name = 'django_irods.tasks.irepl'


class Irm(IRODSTask):
    name = 'django_irods.tasks.irm'


class Irmtrash(IRODSTask):
    name = 'django_irods.tasks.irmtrash'


class Irsync(IRODSTask):
    name = 'django_irods.tasks.irsync'


class Irule(IRODSTask):
    name = 'django_irods.tasks.irule'


class Iscan(IRODSTask):
    name = 'django_irods.tasks.iscan'


class Isysmeta(IRODSTask):
    name = 'django_irods.tasks.isysmeta'


class Itrim(IRODSTask):
    name = 'django_irods.tasks.itrim'


class Iuserinfo(IRODSTask):
    name = 'django_irods.tasks.iuserinfo'


class Ixmsg(IRODSTask):
    name = 'django_irods.tasks.ixmsg'


