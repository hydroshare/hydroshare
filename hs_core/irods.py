import re
from datetime import datetime, timedelta

from django.db import models
from django.core.exceptions import PermissionDenied, ValidationError


class ResourceIRODSMixin(models.Model):
    """ This contains iRODS methods to be included as options for resources """
    class Meta:
        abstract = True

    def create_ticket(self, user, path=None, write=False):
        """
        create an iRODS ticket for reading or modifying a resource

        :param user: user to authorize
        :param path: path in iRODS to the object being requested.
        :return:

        """
        from hs_core.models import ResourceFile 

        # authorize user
        if write:
            if not user.uaccess.can_change_resource(self):
                raise PermissionDenied("user {} cannot change resource {}"
                                       .format(user.username, self.short_id))
        else:
            if not user.uaccess.can_view_resource(self):
                raise PermissionDenied("user {} cannot view resource {}"
                                       .format(user.username, self.short_id))
        if path is None:
            path = self.file_path

        # check validity of path: should point to one of
        # a) bag path
        # b) science metadata.
        # c) resource map.
        # d) a data file
        if path == self.bag_path:
            if write:
                raise PermissionDenied("{} cannot write bag path".format(user.username))
        elif path == self.scimeta_path:
            if write:
                raise PermissionDenied("{} cannot write science metadata file"
                                       .format(user.username))
        elif path == self.resmap_path:
            if write:
                raise PermissionDenied("{} cannot write science metadata file"
                                       .format(user.username))
        else:
            # this will raise an exception if the path into the resource is not acceptable
            # Acceptable paths are data/contents or a subdirectory or subfile.
            ResourceFile.resource_path_is_acceptable(self, path, test_exists=False)

        istorage = self.get_irods_storage()
        read_or_write = 'write' if write else 'read'
        stdout, stderr = istorage.session.run("iticket", None, 'create', read_or_write, path)
        if not stdout.startswith('ticket:'):
            raise ValidationError("ticket creation failed: {}", stderr)
        ticket = stdout.split('\n')[0]
        ticket = ticket[len('ticket:'):]
        _, _ = istorage.session.run('iticket', None, 'mod', ticket,
                                    'uses', '1')

        # This creates a timestamp with a one-hour timeout.
        # TODO: this will fail unless Django and iRODS are both running in UTC. 
        timeout = datetime.now() + timedelta(hours=1) 
        formatted = timeout.strftime("%Y-%m-%d.%H:%M")
        _, _ = istorage.session.run('iticket', None, 'mod', ticket,
                                    'expires', formatted)
        return ticket

    def list_ticket(self, ticket): 
        """ List a ticket's attributes """
        istorage = self.get_irods_storage()
        stdout, stderr = istorage.session.run("iticket", None, 'ls', ticket)
        if stdout.startswith('id:'): 
            stuff = stdout.split('\n')
            output = {}
            for s in stuff: 
                try: 
                    line = s.split(': ') 
                    output[line[0]] = line[1]
                except Exception:  # no : in line
                    pass
            return output
        else:
            raise ValidationError("ticket {} cannot be listed".format(ticket))

    def delete_ticket(self, ticket):
        istorage = self.get_irods_storage()
        _, _ = istorage.session.run('iticket', None, 'delete', ticket)


class ResourceFileIRODSMixin(models.Model):
    """ This contains iRODS functions related to resource files """
    class Meta:
        abstract = True

    def create_ticket(self, user, write=False):
        """ This creates a ticket to read or modify this file """
        return self.resource.create_ticket(user, path=self.storage_path, write=write)
