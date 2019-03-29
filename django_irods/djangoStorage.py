import os
from tempfile import NamedTemporaryFile
from uuid import uuid4
from urllib import urlencode
from django.core.files import File, locks
from django.core.files.storage import Storage

class DjangoStorage(Storage):

        def __init__(self, option = None):
                #init stuff here 
# a. what is icommands?
# b. what is global session and active session?

        def download(self, name):
                return self._open(name, mode='rb')

        def _open(self, name, mode='rb'):
                tmp = NamedTemporaryFile()
                return File(open(tmp.name, mode))

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
        
        def delete(self, name):
                self.session.run("irm", None, "-rf", name)


