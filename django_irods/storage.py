import os
from tempfile import NamedTemporaryFile
from uuid import uuid4

from django.utils.deconstruct import deconstructible
from django.conf import settings
from django.core.files.storage import Storage
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from django_irods import icommands
from icommands import Session, GLOBAL_SESSION, GLOBAL_ENVIRONMENT, SessionException, IRodsEnv


@deconstructible
class IrodsStorage(Storage):
    def __init__(self, option=None):
        if option == 'federated':
            # resource should be saved in federated zone
            self.set_fed_zone_session()
        else:
            self.session = GLOBAL_SESSION
            self.environment = GLOBAL_ENVIRONMENT
            icommands.ACTIVE_SESSION = self.session

    def set_user_session(self, username=None, password=None, host=settings.IRODS_HOST,
                         port=settings.IRODS_PORT, def_res=None, zone=settings.IRODS_ZONE,
                         userid=0, sess_id=None):
        homedir = "/" + zone + "/home/" + username
        userEnv = IRodsEnv(
            pk=userid,
            host=host,
            port=port,
            def_res=def_res,
            home_coll=homedir,
            cwd=homedir,
            username=username,
            zone=zone,
            auth=password,
            irods_default_hash_scheme='MD5'
        )
        if sess_id is None:
            self.session = Session(session_id=uuid4())
            self.environment = self.session.create_environment(myEnv=userEnv)
        else:
            self.session = Session(session_id=sess_id)
            if self.session.session_file_exists():
                self.environment = userEnv
            else:
                self.environment = self.session.create_environment(myEnv=userEnv)

        self.session.run('iinit', None, self.environment.auth)
        icommands.ACTIVE_SESSION = self.session

    # Set iRODS session to wwwHydroProxy for irods_storage input object for iRODS federated
    # zone direct file operations
    def set_fed_zone_session(self):
        if settings.REMOTE_USE_IRODS:
            self.set_user_session(username=settings.HS_WWW_IRODS_PROXY_USER,
                                  password=settings.HS_WWW_IRODS_PROXY_USER_PWD,
                                  host=settings.HS_WWW_IRODS_HOST,
                                  port=settings.IRODS_PORT,
                                  def_res=settings.HS_IRODS_LOCAL_ZONE_DEF_RES,
                                  zone=settings.HS_WWW_IRODS_ZONE,
                                  sess_id='federated_session')

    def delete_user_session(self):
        if self.session != GLOBAL_SESSION and self.session.session_file_exists():
            self.session.delete_environment()

    def download(self, name):
        return self._open(name, mode='rb')

    def getFile(self, src_name, dest_name):
        self.session.run("iget", None, '-f', src_name, dest_name)

    def runBagitRule(self, rule_name, input_path, input_resource):
        """
        run iRODS bagit rule which generated bag-releated files without bundling
        :param rule_name: the iRODS rule name to run
        :param input_path: input parameter to the rule that indicates the collection path to
        create bag for
        :param input_resource: input parameter to the rule that indicates the default resource
        to store generated bag files
        :return: None
        """
        # SessionException will be raised from run() in icommands.py
        self.session.run("irule", None, '-F', rule_name, input_path, input_resource)

    def zipup(self, in_name, out_name):
        """
        run iRODS ibun command to generate zip file for a bag or other folder
        :param in_name: fully qualified irods name of folder to be zipped
        :param out_name: fully qualified irods name of output zipfile.
        :return: None
        """
        # make directory containing output zipfile if necessary
        self.session.run("imkdir", None, '-p', out_name.rsplit('/', 1)[0])
        # SessionException will be raised from run() in icommands.py
        self.session.run("ibun", None, '-cDzip', '-f', out_name, in_name)

    def unzip(self, zip_file_path):
        """
        run iRODS ibun command to unzip files into a new folder
        :param zip_file_path: path of the zipped file to be unzipped
        :return: the folder files were unzipped to
        """

        abs_path = os.path.dirname(zip_file_path)
        unzipped_folder = os.path.splitext(os.path.basename(zip_file_path))[0].strip()
        unzipped_folder = self._get_nonexistant_path(os.path.join(abs_path, unzipped_folder))

        # SessionException will be raised from run() in icommands.py
        self.session.run("ibun", None, '-xDzip', zip_file_path, unzipped_folder)
        return unzipped_folder

    def _get_nonexistant_path(self, path):
        if not self.exists(path):
            return path
        i = 1
        new_path = "{}-{}".format(path, i)
        while self.exists(new_path):
            i += 1
            new_path = "{}-{}".format(path, i)
        return new_path

    def setAVU(self, name, attName, attVal, attUnit=None):
        """
        set AVU on resource collection - this is used for on-demand bagging by indicating
        whether the resource has been modified via AVU pairs

        Parameters:
        :param
        name: the resource collection name to set AVU.
        attName: the attribute name to set
        attVal: the attribute value to set
        attUnit: the attribute Unit to set, default is None, but can be set to
        indicate additional info
        """

        # SessionException will be raised from run() in icommands.py
        if attUnit:
            self.session.run("imeta", None, 'set', '-C', name, attName, attVal, attUnit)
        else:
            self.session.run("imeta", None, 'set', '-C', name, attName, attVal)

    def getAVU(self, name, attName):
        """
        set AVU on resource collection - this is used for on-demand bagging by indicating
        whether the resource has been modified via AVU pairs

        Parameters:
        :param
        name: the resource collection name to set AVU.
        attName: the attribute name to set
        attVal: the attribute value to set
        attUnit: the attribute Unit to set, default is None, but can be set to
        indicate additional info
        """

        # SessionException will be raised from run() in icommands.py
        stdout = self.session.run("imeta", None, 'ls', '-C', name, attName)[0].split("\n")
        ret_att = stdout[1].strip()
        if ret_att == 'None':  # queried attribute does not exist
            return None
        else:
            vals = stdout[2].split(":")
            return vals[1].strip()

    def copyFiles(self, src_name, dest_name, ires=None):
        """
        Parameters:
        :param
        src_name: the iRODS data-object or collection name to be copied from.
        dest_name: the iRODS data-object or collection name to be copied to
        copyFiles() copied an irods data-object (file) or collection (directory)
        to another data-object or collection
        """

        if src_name and dest_name:
            if '/' in dest_name:
                splitstrs = dest_name.rsplit('/', 1)
                if not self.exists(splitstrs[0]):
                    self.session.run("imkdir", None, '-p', splitstrs[0])
            if ires:
                self.session.run("icp", None, '-rf', '-R', ires, src_name, dest_name)
            else:
                self.session.run("icp", None, '-rf', src_name, dest_name)
        return

    def moveFile(self, src_name, dest_name):
        """
        Parameters:
        :param
        src_name: the iRODS data-object or collection name to be moved from.
        dest_name: the iRODS data-object or collection name to be moved to
        moveFile() moves/renames an irods data-object (file) or collection
        (directory) to another data-object or collection
        """
        if src_name and dest_name:
            if '/' in dest_name:
                splitstrs = dest_name.rsplit('/', 1)
                if not self.exists(splitstrs[0]):
                    self.session.run("imkdir", None, '-p', splitstrs[0])
            self.session.run("imv", None, src_name, dest_name)
        return

    def saveFile(self, from_name, to_name, create_directory=False, data_type_str=''):
        """
        Parameters:
        :param
        from_name: the temporary file name in local disk to be uploaded from.
        to_name: the data object path in iRODS to be uploaded to
        create_directory: create directory as needed when set to True. Default is False
        Note if only directory needs to be created without saving a file, from_name should be empty
        and to_name should have "/" as the last character
        """
        if create_directory:
            splitstrs = to_name.rsplit('/', 1)
            self.session.run("imkdir", None, '-p', splitstrs[0])
            if len(splitstrs) <= 1:
                return

        if from_name:
            try:
                if data_type_str:
                    self.session.run("iput", None, '-D', data_type_str, '-f', from_name, to_name)
                else:
                    self.session.run("iput", None, '-f', from_name, to_name)
            except:
                if data_type_str:
                    self.session.run("iput", None, '-D', data_type_str, '-f', from_name, to_name)
                else:
                    # IRODS 4.0.2, sometimes iput fails on the first try.
                    # A second try seems to fix it.
                    self.session.run("iput", None, '-f', from_name, to_name)
        return

    def _open(self, name, mode='rb'):
        tmp = NamedTemporaryFile()
        self.session.run("iget", None, '-f', name, tmp.name)
        return tmp

    def _save(self, name, content):
        self.session.run("imkdir", None, '-p', name.rsplit('/', 1)[0])
        with NamedTemporaryFile(delete=False) as f:
            for chunk in content.chunks():
                f.write(chunk)
            f.flush()
            f.close()
            try:
                self.session.run("iput", None, '-f', f.name, name)
            except:
                # IRODS 4.0.2, sometimes iput fails on the first try. A second try seems to fix it.
                self.session.run("iput", None, '-f', f.name, name)
            os.unlink(f.name)
        return name

    def delete(self, name):
        self.session.run("irm", None, "-rf", name)

    def exists(self, name):
        try:
            stdout = self.session.run("ils", None, name)[0]
            return stdout != ""
        except SessionException:
            return False

    def listdir(self, path):
        stdout = self.session.run("ils", None, path)[0].split("\n")
        listing = ([], [])
        directory = stdout[0][0:-1]
        directory_prefix = "  C- " + directory + "/"
        for i in range(1, len(stdout)):
            if stdout[i][:len(directory_prefix)] == directory_prefix:
                dirname = stdout[i][len(directory_prefix):].strip()
                if dirname:
                    listing[0].append(dirname)
            else:
                filename = stdout[i].strip()
                if filename:
                    listing[1].append(filename)
        return listing

    def size(self, name):
        stdout = self.session.run("ils", None, "-l", name)[0].split()
        return int(stdout[3])

    def url(self, name):
        return reverse('django_irods.views.download', kwargs={'path': name})

    def get_available_name(self, name):
        """
        Reject duplicate file names rather than renaming them.
        """
        if self.exists(name):
            raise ValidationError(str.format("File {} already exists.", name))
        return name
