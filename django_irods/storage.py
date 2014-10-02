from django.conf import settings
from django.core.files.storage import Storage
from tempfile import NamedTemporaryFile
from icommands import Session, GLOBAL_SESSION, SessionException
import os

class IrodsStorage(Storage):
    def __init__(self, option=None):
        self.session = GLOBAL_SESSION if getattr(settings, 'IRODS_GLOBAL_SESSION', False) else Session()
        if self.session != GLOBAL_SESSION:
            self.session.run('iinit', None, self.session.create_environment().auth)

    def _open(self, name, mode='rb'):
        tmp = NamedTemporaryFile()
        self.session.run("iget", None, '-f', name, tmp.name)
        return tmp

    def _save(self, name, content):
        self.session.run("imkdir", None, '-p', name.rsplit('/',1)[0])
        with NamedTemporaryFile(delete=False) as f:
            for chunk in content.chunks():
                f.write(chunk)
            f.flush()
            f.close()
            try:
                self.session.run("iput", None, f.name, name)
            except:
                self.session.run("iput", None, f.name, name) # IRODS 4.0.2, sometimes iput fails on the first try.  A second try seems to fix it.
            os.unlink(f.name)
        return name

    def delete(self, name):
        self.session.run("irm", None, "-f", name)

    def exists(self, name):
        try:
            stdout = self.session.run("ils", None, name)[0]
            return stdout != ""
        except SessionException:
            return False

    def listdir(self, path):
        stdout = self.session.run("ils", None, path)[0].split("\n")
        listing = ( [], [] )
        directory = stdout[0][0:-2]
        directory_prefix = "  C- " + directory + "/"
        for i in range(1, len(stdout)):
            if stdout[i][:len(directory_prefix)] == directory_prefix:
                listing[0].append(stdout[i][len(directory_prefix):])
            else:
                listing[1].append(stdout[i].strip)
        return listing

    def size(self, name):
        stdout = self.session.run("ils", None, "-l", name)[0].split()
        return int(stdout[3])

    def url(self, name):
        return "/django_irods/download/?path={name}".format(name=name)

