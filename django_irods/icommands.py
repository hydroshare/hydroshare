"""Originally written by Antoine deTorcy"""

import os
import shutil
import subprocess
import textwrap
from cStringIO import StringIO
from django.conf import settings
from collections import namedtuple

class SessionException(Exception):
    def __init__(self, exitcode, stdout, stderr):
        super(SessionException, self).__init__(self, "Error processing IRODS request: {exitcode}. stderr follows:\n\n{stderr}".format(
            exitcode=exitcode,stderr=stderr
        ))
        self.stdout = stdout
        self.stderr = stderr
        self.exitcode = exitcode

IRodsEnv = namedtuple(
    'IRodsEnv',
    ['pk','host','port','def_res','home_coll','cwd','username','zone','auth']
)

class Session(object):
    """A set of methods to start, close and manage multiple
    iRODS client sessions at the same time, using icommands.
    """

    def __init__(self, root=None, icommands_path=None, session_id = 'default_session'):
        self.root = root or settings.IRODS_ROOT  # main directory to store session and log dirs
        self.icommands_path = icommands_path or settings.IRODS_ICOMMANDS_PATH # where the icommand binaries are
        self.session_id = session_id
        self.session_path = "{root}/{session_id}".format(root=self.root, session_id=self.session_id)

    def create_environment(self, myEnv=None):
        """Creates session files in temporary directory.

        Argument myEnv must be instance of RodsEnv defined above.
        This method is to be called prior to calling self.runCmd('iinit').
        """
        # will have to add some testing for existing files
        # and acceptable argument values
        try:
            os.makedirs(self.session_path)
        except OSError:
            pass

        if not myEnv:
            myEnv = IRodsEnv(
               pk=-1,
               host=settings.IRODS_HOST,
               port=settings.IRODS_PORT,
               def_res=settings.IRODS_DEFAULT_RESOURCE,
               home_coll=settings.IRODS_HOME_COLLECTION,
               cwd=settings.IRODS_CWD,
               username=settings.IRODS_USERNAME,
               zone=settings.IRODS_ZONE,
               auth=settings.IRODS_AUTH
            )

        # create .irodsEnv file
        env_path = "{session_path}/.irodsEnv".format(session_path=self.session_path)
        with open(env_path, "w") as env_file:
            env_file.write(textwrap.dedent("""\
                irodsHost '{host}'
                irodsPort '{port}'
                irodsDefResource '{def_res}'
                irodsHome '{home_coll}'
                irodsCwd '{cwd}'
                irodsUserName '{username}'
                irodsZone '{zone}'
            """).format(
                host=myEnv.host,
                port=myEnv.port,
                def_res=myEnv.def_res,
                home_coll=myEnv.home_coll,
                username=myEnv.username,
                cwd=myEnv.cwd,
                zone=myEnv.zone
            ))
        return myEnv

    def delete_environment(self):
        """Deletes temporary sessionDir recursively.

        To be called after self.runCmd('iexit').
        """
        shutil.rmtree(self.session_path)

    def session_file_exists(self):
        """Checks for the presence of .irodsEnv in temporary sessionDir.
        """
        try:
            if os.path.exists(os.path.join(self.session_path, '.irodsEnv')):
                return True
        except:
            return False
        else:
            return False

    @property
    def zone(self):
        """Returns current zone name from .irodsEnv or an empty string
        if the file does not exist.
        """
        zone_name = ""
        if not self.session_file_exists():
            return zone_name
        envfilename = "%s/.irodsEnv" % (self.session_path)
        envfile = open(envfilename)
        for line in envfile:
            if 'irodsZone' in line:
                zone_name = line.split()[1]
        envfile.close()
        return zone_name

    @property
    def username(self):
        """Returns current irodsUserName from .irodsEnv or an empty string
        if the file does not exist.
        """
        user_name = ""
        if not self.session_file_exists():
            return user_name
        envfilename = os.path.join(self.session_path, ".irodsEnv")
        envfile = open(envfilename)
        for line in envfile:
            if 'irodsUserName' in line:
                user_name = line.split()[1]
        envfile.close()
        return user_name

    def run(self, icommand, data=None, *args):
        """Runs an icommand with optional argument list and
        returns tuple (stdout, stderr) from subprocess execution.

        Set of valid commands can be extended.
        """

        myenv = os.environ.copy()
        myenv['irodsEnvFile'] = os.path.join(self.session_path, ".irodsEnv")
        myenv['irodsAuthFileName'] = os.path.join(self.session_path, ".irodsA")

        cmdStr = os.path.join(self.icommands_path, icommand)
        argList = [cmdStr]
        argList.extend(args)

        if icommand != 'iinit' and GLOBAL_SESSION:
            self.run('iinit', None, GLOBAL_ENVIRONMENT.auth)

        stdin=None
        if data:
            stdin = StringIO(data)

        proc = subprocess.Popen(
            argList,
            stdin=subprocess.PIPE if stdin else None,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            env = myenv
        )
        stdout, stderr = proc.communicate(input=data) if stdin else proc.communicate()

        if proc.returncode:
            raise SessionException(proc.returncode, stdout, stderr)
        else:
            return stdout, stderr

    def run_safe(self, icommand, data=None, *args):
        myenv = os.environ.copy()
        myenv['irodsEnvFile'] = os.path.join(self.session_path, ".irodsEnv")
        myenv['irodsAuthFileName'] = os.path.join(self.session_path, ".irodsA")

        cmdStr = os.path.join(self.icommands_path, icommand)
        argList = [cmdStr]
        argList.extend(args)

        stdin=None
        if data:
            print data
            stdin = StringIO(data)

        proc = subprocess.Popen(
            argList,
            stdin=stdin,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            env = myenv
        )
        return proc

    def runbatch(self, *icommands):
        myenv = os.environ.copy()
        myenv['irodsEnvFile'] = os.path.join(self.session_path, ".irodsEnv")
        myenv['irodsAuthFileName'] = os.path.join(self.session_path, ".irodsA")
        return_codes = []

        for icommand, args in icommands:
            cmdStr = os.path.join(self.icommands_path, icommand)
            argList = [cmdStr]
            argList.extend(args)

            return_codes.append(subprocess.Popen(
                argList,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                env = myenv
            ).communicate())
        return return_codes

    def admin(self, *args):
        """Runs the iadmin icommand with optional argument list and
        returns tuple (stdout, stderr) from subprocess execution.
        """

        # should probably also add a condition to restrict
        # possible values for icommandsDir
        myenv = os.environ.copy()
        myenv['irodsEnvFile'] = "%s/.irodsEnv" % (self.session_path)
        myenv['irodsAuthFileName'] = "%s/.irodsA" % (self.session_path)

        cmdStr = "{icommands}/iadmin".format(icommands=self.icommands_path)

        argList = [cmdStr]
        argList.extend(args)

        return subprocess.Popen(
            argList,
            stdin = "yes\n",
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            env = myenv
        ).communicate()

if settings.IRODS_GLOBAL_SESSION:
    GLOBAL_SESSION = Session()
    GLOBAL_ENVIRONMENT = GLOBAL_SESSION.create_environment()
    GLOBAL_SESSION.run('iinit', None, GLOBAL_ENVIRONMENT.auth)
else:
    GLOBAL_SESSION = None

### an example usage
#def testsuite():
#    working_path = "/Users/trel/Desktop/irodstesting/sessions"
#    icommands_bin = "/Users/trel/Desktop/irodstesting/iRODS/clients/icommands/bin"
#    session_id = datetime.datetime.now().strftime("%Y%m%dT%H%M%S.%f")
#    userInfo = RodsEnv( 'trelpancake',
#                        '1247',
#                        'trelpancakeResource',
#                        '/tempZone/home/rods',
#                        '/tempZone/home/rods',
#                        'rods',
#                        'tempZone',
#                        'rods')
#    mysession = RodsSession(working_path, icommands_bin, session_id)
#    mysession.createEnvFiles(userInfo)
#
#    mysession.runCmd('iinit', [userInfo.auth])
#
#    output =  mysession.runCmd('ils')
#    print output[0]
#
#    print "\nimeta ls -d beetle.jpg:\n"
#    output = mysession.runCmd('imeta',['ls', '-d', 'beetle.jpg'])
#    print output[0]
#
#    mysession.runCmd('icd',['testcoll0'])
#
#    output =  mysession.runCmd('ils')
#    print output[0]
#
#    mysession.runCmd('icd',['..'])
#
#    print "\nimeta ls -C testcoll0:\n"
#    output = mysession.runCmd('imeta',['ls', '-C', 'testcoll0'])
#    print output[0]
#
#    mysession.runCmd('iexit', ['full'])
#    mysession.deleteEnvFiles()