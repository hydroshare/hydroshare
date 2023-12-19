import os
from datetime import datetime
from dateutil import tz

from tempfile import NamedTemporaryFile
from uuid import uuid4
from urllib.parse import urlencode

from django.utils.deconstruct import deconstructible
from django.conf import settings
from django.core.files.storage import Storage
from django.urls import reverse
from django.core.exceptions import ValidationError

from django_irods import icommands
from .icommands import (
    Session,
    GLOBAL_SESSION,
    GLOBAL_ENVIRONMENT,
    SessionException,
    IRodsEnv,
)


@deconstructible
class IrodsStorage(Storage):
    def __init__(self, option=None):
        if option == "federated":
            # resource should be saved in federated zone
            self.set_fed_zone_session()
        else:
            self.session = GLOBAL_SESSION
            self.environment = GLOBAL_ENVIRONMENT
            icommands.ACTIVE_SESSION = self.session

    @property
    def getUniqueTmpPath(self):
        # return a unique temporary path under IRODS_ROOT directory
        return os.path.join(getattr(settings, "IRODS_ROOT", "/tmp"), uuid4().hex)

    @staticmethod
    def get_absolute_path_query(path, parent=False):
        """
        Get iquest query string that needs absolute path of the input path for the HydroShare iRODS data zone
        :param path: input path to be converted to absolute path if needed
        :param parent: indicating whether query string should be checking COLL_PARENT_NAME rather than COLL_NAME
        :return: iquest query string that has the logical path of the input path as input
        """

        # iquest has a bug that cannot handle collection name containing single quote as reported here
        # https://github.com/irods/irods/issues/4887. This is a work around and can be removed after the bug is fixed
        if "'" in path:
            path = path.replace("'", "%")
            qry_str = "COLL_PARENT_NAME like '{}'" if parent else "COLL_NAME like '{}'"
        else:
            qry_str = "COLL_PARENT_NAME = '{}'" if parent else "COLL_NAME = '{}'"

        if os.path.isabs(path):
            # iRODS federated logical path which is already absolute path
            return qry_str.format(path)
        return qry_str.format(os.path.join(settings.IRODS_HOME_COLLECTION, path))

    def set_user_session(
        self,
        username=None,
        password=None,
        host=settings.IRODS_HOST,
        port=settings.IRODS_PORT,
        def_res=None,
        zone=settings.IRODS_ZONE,
        userid=0,
        sess_id=None,
    ):
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
            irods_default_hash_scheme="MD5",
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

        self.session.run("iinit", None, self.environment.auth)
        icommands.ACTIVE_SESSION = self.session

    # Set iRODS session to wwwHydroProxy for irods_storage input object for iRODS federated
    # zone direct file operations
    def set_fed_zone_session(self):
        if settings.REMOTE_USE_IRODS:
            self.set_user_session(
                username=settings.IRODS_USERNAME,
                password=settings.IRODS_AUTH,
                host=settings.IRODS_HOST,
                port=settings.IRODS_PORT,
                def_res=settings.HS_IRODS_USER_ZONE_DEF_RES,
                zone=settings.IRODS_ZONE,
                sess_id="federated_session",
            )

    def delete_user_session(self):
        if self.session != GLOBAL_SESSION and self.session.session_file_exists():
            self.session.delete_environment()

    def download(self, name):
        return self._open(name, mode="rb")

    def getFile(self, src_name, dest_name):
        self.session.run("iget", None, "-f", src_name, dest_name)

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
        self.session.run("irule", None, " -r", "irods_rule_engine_plugin-irods_rule_language-instance", "-F", rule_name, input_path, input_resource)

    def zipup(self, in_name, out_name):
        """
        run iRODS ibun command to generate zip file for the bag
        :param in_name: input parameter to indicate the collection path to generate zip
        :param out_name: the output zipped file name
        :return: None
        """
        self.session.run("imkdir", None, "-p", out_name.rsplit("/", 1)[0])
        # SessionException will be raised from run() in icommands.py
        self.session.run("ibun", None, "-cDzip", "-f", out_name, in_name)

    def unzip(self, zip_file_path, unzipped_folder=""):
        """
        run iRODS ibun command to unzip files into a new folder
        :param zip_file_path: path of the zipped file to be unzipped
        :param unzipped_folder: Optional defaults to the basename of zip_file_path when not
        provided.  The folder to unzip to.
        :return: the folder files were unzipped to
        """

        abs_path = os.path.dirname(zip_file_path)
        if not unzipped_folder:
            unzipped_folder = abs_path
        else:
            unzipped_folder = self._get_nonexistant_path(
                os.path.join(abs_path, unzipped_folder)
            )

        # SessionException will be raised from run() in icommands.py
        self.session.run("ibun", None, "-xDzip", zip_file_path, unzipped_folder)
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
            self.session.run("imeta", None, "set", "-C", name, attName, attVal, attUnit)
        else:
            self.session.run("imeta", None, "set", "-C", name, attName, attVal)

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
        stdout = self.session.run("imeta", None, "ls", "-C", name, attName)[0].split(
            "\n"
        )
        ret_att = stdout[1].strip()
        if ret_att == "None":  # queried attribute does not exist
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
            if "/" in dest_name:
                splitstrs = dest_name.rsplit("/", 1)
                if not self.exists(splitstrs[0]):
                    self.session.run("imkdir", None, "-p", splitstrs[0])
            if ires:
                self.session.run("icp", None, "-rf", "-R", ires, src_name, dest_name)
            else:
                self.session.run("icp", None, "-rf", src_name, dest_name)
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
            if "/" in dest_name:
                splitstrs = dest_name.rsplit("/", 1)
                if not self.exists(splitstrs[0]):
                    self.session.run("imkdir", None, "-p", splitstrs[0])
            self.session.run("imv", None, src_name, dest_name)
        return

    def saveFile(self, from_name, to_name, create_directory=False, data_type_str=""):
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
            splitstrs = to_name.rsplit("/", 1)
            self.session.run("imkdir", None, "-p", splitstrs[0])
            if len(splitstrs) <= 1:
                return

        if from_name:
            try:
                if data_type_str:
                    self.session.run(
                        "iput", None, "-D", data_type_str, "-f", from_name, to_name
                    )
                else:
                    self.session.run("iput", None, "-f", from_name, to_name)
            except: # noqa
                if data_type_str:
                    self.session.run(
                        "iput", None, "-D", data_type_str, "-f", from_name, to_name
                    )
                else:
                    # IRODS 4.0.2, sometimes iput fails on the first try.
                    # A second try seems to fix it.
                    self.session.run("iput", None, "-f", from_name, to_name)
        return

    def _open(self, name, mode="rb"):
        tmp = NamedTemporaryFile()
        self.session.run("iget", None, "-f", name, tmp.name)
        return tmp

    def _save(self, name, content):
        self.session.run("imkdir", None, "-p", name.rsplit("/", 1)[0])
        with NamedTemporaryFile(delete=False) as f:
            for chunk in content.chunks():
                f.write(chunk)
            f.flush()
            f.close()
            try:
                self.session.run("iput", None, "-f", f.name, name)
            except: # noqa
                # IRODS 4.0.2, sometimes iput fails on the first try. A second try seems to fix it.
                self.session.run("iput", None, "-f", f.name, name)
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

    def _list_files(self, path):
        """
        internal method to only list data objects/files under path
        :param path: iRODS collection/directory path
        :return: ordered filename_list and filesize_list
        """

        fname_list = []
        fsize_list = []

        # the query below returns name and size (separated in comma) of all data
        # objects/files under the path collection/directory
        qrystr = (
            "select DATA_NAME, DATA_SIZE where DATA_REPL_STATUS != '0' "
            "AND {}".format(IrodsStorage.get_absolute_path_query(path))
        )
        stdout = self.session.run("iquest", None, "--no-page", "%s,%s", qrystr)[
            0
        ].split("\n")

        for i in range(len(stdout)):
            if not stdout[i] or "CAT_NO_ROWS_FOUND" in stdout[i]:
                break
            file_info = stdout[i].rsplit(",", 1)
            fname_list.append(file_info[0])
            fsize_list.append(file_info[1])

        return fname_list, fsize_list

    def _list_subdirs(self, path):
        """
        internal method to only list sub-collections/sub-directories under path
        :param path: iRODS collection/directory path
        :return: sub-collection/directory name list
        """
        subdir_list = []
        # the query below returns name of all sub-collections/sub-directories
        # under the path collection/directory

        qrystr = "select COLL_NAME where {}".format(
            IrodsStorage.get_absolute_path_query(path, parent=True)
        )
        stdout = self.session.run("iquest", None, "--no-page", "%s", qrystr)[0].split(
            "\n"
        )
        for i in range(len(stdout)):
            if not stdout[i] or "CAT_NO_ROWS_FOUND" in stdout[i]:
                break
            dirname = stdout[i]
            # remove absolute path prefix to only show relative sub-dir name
            idx = dirname.find(path)
            if idx > 0:
                dirname = dirname[idx + len(path) + 1 :]

            subdir_list.append(dirname)

        return subdir_list

    def listdir(self, path):
        """
        return list of sub-collections/sub-directories, data objects/files and their sizes
        :param path: iRODS collection/directory path
        :return: (sub_directory_list, file_name_list, file_size_list)
        """
        # remove any trailing slashes if any; otherwise, iquest would fail
        path = path.strip()
        while path.endswith("/"):
            path = path[:-1]

        # check first whether the path is an iRODS collection/directory or not, and if not, need
        # to raise SessionException, and if yes, can proceed to get files and sub-dirs under it
        qrystr = "select COLL_NAME where {}".format(
            IrodsStorage.get_absolute_path_query(path)
        )
        stdout = self.session.run("iquest", None, "%s", qrystr)[0]
        if "CAT_NO_ROWS_FOUND" in stdout:
            raise SessionException(-1, "", "folder {} does not exist".format(path))

        fname_list, fsize_list = self._list_files(path)

        subdir_list = self._list_subdirs(path)

        listing = (subdir_list, fname_list, fsize_list)

        return listing

    def size(self, name):
        """
        return the size of the data object/file with file name being passed in
        :param name: file name
        :return: the size of the file
        """
        file_info = name.rsplit("/", 1)
        if len(file_info) < 2:
            raise ValidationError(
                "{} is not a valid file path to retrieve file size "
                "from iRODS".format(name)
            )
        coll_name = file_info[0]
        file_name = file_info[1]
        qrystr = (
            "select DATA_SIZE where DATA_REPL_STATUS != '0' AND "
            "{} AND DATA_NAME = '{}'".format(
                IrodsStorage.get_absolute_path_query(coll_name), file_name
            )
        )
        stdout = self.session.run("iquest", None, "%s", qrystr)[0]

        if "CAT_NO_ROWS_FOUND" in stdout:
            raise ValidationError(
                "{} cannot be found in iRODS to retrieve " "file size".format(name)
            )
        # remove potential '\n' from stdout
        size_string = stdout.strip("0\n").replace("\n", "")
        try:
            ret = int(float(size_string))
            return ret
        except ValueError:
            return 0

    def checksum(self, full_name, force_compute=True):
        """
        Compute/Update checksum of file object and return the checksum
        :param full_name: the data object name with full collection path in order to locate data object from current
        working directory
        :return: checksum of the file object
        """
        # first force checksum (re)computation
        if force_compute:
            self.session.run("ichksum", None, "-f", full_name)
        # retrieve checksum using iquest
        # get data object name only from the full_name input parameter to be used by iquest
        if "/" in full_name:
            file_info = full_name.rsplit("/", 1)
            coll_name_query = IrodsStorage.get_absolute_path_query(file_info[0])
            obj_name = file_info[1]
        else:
            coll_name_query = "COLL_NAME = '{}'".format(settings.IRODS_HOME_COLLECTION)
            obj_name = full_name

        qrystr = "SELECT DATA_CHECKSUM WHERE {} AND DATA_NAME = '{}'".format(
            coll_name_query, obj_name
        )
        stdout = self.session.run("iquest", None, "%s", qrystr)[0]
        if "CAT_NO_ROWS_FOUND" in stdout:
            raise ValidationError(
                "{} cannot be found in iRODS to retrieve " "checksum".format(obj_name)
            )
        # remove potential '\n' from stdout
        checksum = stdout.strip("\n")
        if not checksum:
            if force_compute:
                raise ValidationError(
                    "checksum for {} cannot be found in iRODS".format(obj_name)
                )
            # checksum hasn't been computed, so force the checksum computation
            return self.checksum(full_name, force_compute=True)
        return checksum

    def url(self, name, url_download=False, zipped=False, aggregation=False):
        reverse_url = reverse("rest_download", kwargs={"path": name})
        query_params = {
            "url_download": url_download,
            "zipped": zipped,
            "aggregation": aggregation,
        }
        return reverse_url + "?" + urlencode(query_params)

    def get_available_name(self, name, max_length=None):
        """
        Reject duplicate file names rather than renaming them.
        """
        if self.exists(name):
            raise ValidationError(str.format("File {} already exists.", name))
        return name

    def get_modified_time(self, name):
        """
        Return the last modified time (as a datetime in UTC timezone) of the file specified by full_name.
        :param name: data object (file) name with full collection path in order to locate file from current
        working directory
        :return: last modified time of the file in UTC timezone
        """
        if "/" in name:
            file_info = name.rsplit("/", 1)
            coll_name_query = IrodsStorage.get_absolute_path_query(file_info[0])
            obj_name = file_info[1]
        else:
            coll_name_query = "COLL_NAME = '{}'".format(settings.IRODS_HOME_COLLECTION)
            obj_name = name
        qrystr = "SELECT DATA_MODIFY_TIME WHERE {} AND DATA_NAME = '{}'".format(
            coll_name_query, obj_name
        )
        stdout = self.session.run("iquest", None, "%s", qrystr)[0]
        if "CAT_NO_ROWS_FOUND" in stdout:
            raise ValidationError("{} cannot be found in iRODS".format(name))
        # remove potential '\n' from stdout
        timestamp = float(stdout.split("\n", 1)[0])
        utc_dt = datetime.fromtimestamp(timestamp, tz.UTC)
        return utc_dt

    def isFile(self, path):
        try:
            self.listdir(path)
            return False
        except SessionException:
            return True

    def isDir(self, path):
        return not self.isFile(path)
