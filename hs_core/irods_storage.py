from django.conf import settings
from django.core.files.storage import Storage
#from django.utils.deconstruct import deconstructible
from icommands import RodsSession
from tempfile import NamedTemporaryFile

#@deconstructible
class IrodsStorage(Storage):
    def __init__(self, option=None):
        self.session = RodsSession( "./", "/usr/bin" )
        self.session.runCmd( "iinit" );
        if not option:
            option = settings.CUSTOM_STORAGE_OPTIONS

    def _open(name, mode='rb'):
        self.session.runCmd( "iget", [ name, "tempfile." + name] )
        return open(name)

    def _save(name, content):
        self.session.runCmd( "iput", [ content.name, name ] )
        return name

    def delete(name):
        self.session.runCmd( "irm", [ "-f", name ] )

    def exists(name):
        stdout = self.session.runCmd( "ils", [ name ] )[0]
        return stdout != ""

    def listdir(path):
        stdout = self.session.runCmd( "ils", [ name ] )[0].split("\n")
        listing = ( [], [] )
        directory = stdout[0][0:-2]
        directory_prefix = "  C- " + directory + "/"
        for i in range(1, len(stdout)):
            if stdout[i][:len(directory_prefix)] == directory_prefix:
                listing[0].append(stdout[i][len(directory_prefix):])
            else:
                listing[1].append(stdout[i].strip)
        return listing

    def size(name):
        stdout = self.session.runCmd( "ils", [ "-l", name ] )[0].split()
        return int(stdout[1])

    def url(name):
        return "/hsapi/_internal/file/" + name
