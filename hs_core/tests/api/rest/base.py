import socket
import json

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users
from hs_core.hydroshare import resource


class HSRESTTestCase(APITestCase):

    def setUp(self):
        self.hostname = socket.gethostname()
        self.resource_url = "http://example.com/resource/{res_id}/"
        self.maxDiff = None
        self.client = APIClient()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False)

        self.client.force_authenticate(user=self.user)

        self.resources_to_delete = []

    def tearDown(self):
        for r in self.resources_to_delete:
            resource.delete_resource(r)

        self.user.delete()

    def getResourceBag(self, res_id, exhaust_stream=True):
        """Get resource bag from iRODS, following redirects.

        :param res_id: ID of resource whose bag should be fetched
        :param exhaust_stream: If True, the response returned
           will have its stream_content exhausted.  This prevents
           an error that causes the Docker container to exit when tests
           are run with an external web server.
        :return: Django test client response object
        """
        url = "/hsapi/resource/{res_id}".format(res_id=res_id)
        return self._get_file_irods(url, exhaust_stream)

    def getDownloadTaskStatus(self, task_id):
        """Check download celery task status.

        :param task_id: ID of download celery task
        :return: Django test client response object
        """
        url = reverse('get_task_status', kwargs={'task_id': task_id})
        return self.client.get(url, follow=True)


    def getResourceFile(self, res_id, file_name, exhaust_stream=True):
        """Get resource file from iRODS, following redirects

        :param res_id: ID of resource whose resource file should be fetched
        :param file_name: Name of the file to fetch (just the filename, not the full path)
        :param exhaust_stream: If True, the response returned
           will have its stream_content exhausted.  This prevents
           an error that causes the Docker container to exit when tests
           are run with an external web server.
        :return: Django test client response object
        """
        url = "/hsapi/resource/{res_id}/files/{file_name}".format(res_id=res_id,
                                                                  file_name=file_name)
        return self._get_file_irods(url, exhaust_stream)

    def _get_file_irods(self, url, exhaust_stream=True):
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Exhaust the file stream so that WSGI doesn't get upset (this causes the Docker container to exit)
        if exhaust_stream and hasattr(response, 'streaming_content'):
            for l in response.streaming_content:
                pass

        return response

    def getScienceMetadata(self, res_id, exhaust_stream=True):
        """Get sciencematadata.xml from iRODS, following redirects

        :param res_id: ID of resource whose science metadata should be fetched
        :param exhaust_stream: If True, the response returned
           will have its stream_content exhausted.  This prevents
           an error that causes the Docker container to exit when tests
           are run with an external web server.
        :return: Django test client response object
        """
        url = "/hsapi/scimeta/{res_id}/".format(res_id=res_id)
        response = self._get_file_irods(url, exhaust_stream)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertGreater(int(response['Content-Length']), 0)

        return response


class SciMetaTestCase(HSRESTTestCase):

    NS = {'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
          'rdfs1': "http://www.w3.org/2001/01/rdf-schema#",
          'dc': "http://purl.org/dc/elements/1.1/",
          'dcterms': "http://purl.org/dc/terms/",
          'hsterms': "http://hydroshare.org/terms/"}

    RESOURCE_URL_TEMPLATE = "http://example.com/resource/{0}"

    RESOURCE_METADATA = 'resourcemetadata.xml'
    RESOURCE_METADATA_OLD = 'resourcemetadata_old.xml'
    RESOURCE_METADATA_UPDATED = 'resourcemetadata_updated.xml'

    def getTitle(self, scimeta, should_exist=True):
        """ Get title from parsed ElementTree representation of science metadata.

        :param scimeta: ElementTree representing science metadata
        :param should_exist: If True, the abstract is expected to exist in the DOM.
        :return: String representing title text, if should_exist == True, else None.
        """
        title = scimeta.xpath('/rdf:RDF/rdf:Description[1]/dc:title', namespaces=self.NS)

        if should_exist:
            self.assertEqual(len(title), 1)
            return title[0].text
        else:
            self.assertEqual(len(title), 0)

        return None

    def getAbstract(self, scimeta, should_exist=True):
        """ Get abstract from parsed ElementTree representation of science metadata.

        :param scimeta: ElementTree representing science metadata
        :param should_exist: If True, the abstract is expected to exist in the DOM.
        :return: String representing abstract text, if should_exist == True, else None.
        """
        abstract = scimeta.xpath('/rdf:RDF/rdf:Description[1]/dc:description/rdf:Description/dcterms:abstract',
                                 namespaces=self.NS)
        if should_exist:
            self.assertEqual(len(abstract), 1)
            return abstract[0].text
        else:
            self.assertEqual(len(abstract), 0)

        return None

    def getKeywords(self, scimeta):
        """ Get keywords from parsed ElementTree representation of science metadata.

        :param scimeta: ElementTree representing science metadata
        :return: Tuple of Strings representing keyword metadata elements
        """
        keywords = scimeta.xpath('/rdf:RDF/rdf:Description[1]/dc:subject',
                                 namespaces=self.NS)
        return tuple(k.text for k in keywords)

    def updateScimetaResourceID(self, scimeta, new_id):
        """ Update resource ID of the science metadata to http://example.com/resource/$new_id

        :param scimeta: ElementTree representing science metadata
        :param new_id: String representing the new ID of the resource.
        :return: ElementTree representing science metadata
        """
        desc = scimeta.xpath('/rdf:RDF/rdf:Description[1]', namespaces=self.NS)[0]
        desc.set('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about',
                 self.RESOURCE_URL_TEMPLATE.format(new_id))
        return scimeta

    def updateScimeta(self, pk, scimeta_path, should_succeed=True):
        """ Use the test client to perform a PUT /scimeta
        using scimeta_path as the resourcemetadata.xml

        :param pk: The ID of the resource whose
        :param scimeta_path: Path to a file named resourcemetadata.xml
        :param should_succeed: If True, will check for HTTP 202 status in the
        response, else will check for HTTP 400.
        :return: Test client HTTP response.
        """
        params = {'file': (self.RESOURCE_METADATA,
                          open(scimeta_path),
                          'application/xml')}
        url = "/hsapi/scimeta/{pid}/".format(pid=pk)
        response = self.client.put(url, params)
        if should_succeed:
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED,
                             msg=str(json.loads(response.content)))
        else:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                             msg=str(json.loads(response.content)))

        return response


class ModelInstanceSciMetaTestCase(SciMetaTestCase):

    MOD_OUT_PATH = ('/rdf:RDF/rdf:Description[1]/hsterms:ModelOutput/'
                    'rdf:Description/hsterms:includesModelOutput')
    EXECUTED_BY_PATH = ('/rdf:RDF/rdf:Description[1]/hsterms:ExecutedBY/'
                        'rdf:Description')
    EXECUTED_BY_NAME_PATH = "{exec_by_path}/hsterms:modelProgramName".format(exec_by_path=EXECUTED_BY_PATH)
    EXECUTED_BY_ID_PATH = "{exec_by_path}/hsterms:modelProgramIdentifier".format(exec_by_path=EXECUTED_BY_PATH)

    def setUp(self):
        super(ModelInstanceSciMetaTestCase, self).setUp()

        self.rtype_prog = 'ModelProgramResource'
        self.title_prog = 'Some program'
        res = resource.create_resource(self.rtype_prog,
                                       self.user,
                                       self.title_prog)
        self.pid_prog = res.short_id
        self.resources_to_delete.append(self.pid_prog)

    def updateExecutedBy(self, scimeta, name, id):
        """ Update ExecutedBy

        :param scimeta: ElementTree representing science metadata
        :param name: String representing the title of the program resource.
        :param id: String representing the ID of the program resource.
        :return: ElementTree representing science metadata
        """
        name_elem = scimeta.xpath(self.EXECUTED_BY_NAME_PATH, namespaces=self.NS)[0]
        name_elem.text = name

        id_elem = scimeta.xpath(self.EXECUTED_BY_ID_PATH, namespaces=self.NS)[0]
        id_elem.text = self.RESOURCE_URL_TEMPLATE.format(id) + '/'

        return scimeta


class ResMapTestCase(HSRESTTestCase):

    NS = {'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
          'rdfs1': "http://www.w3.org/2001/01/rdf-schema#",
          'dc': "http://purl.org/dc/elements/1.1/",
          'dcterms': "http://purl.org/dc/terms/",
          'hsterms': "http://hydroshare.org/terms/"}

    RESOURCE_URL_TEMPLATE = "http://example.com/resource/{0}"

    RESOURCE_METADATA = 'resourcemap.xml'
    RESOURCE_METADATA_OLD = 'resourcemap_old.xml'
    RESOURCE_METADATA_UPDATED = 'resourcemap_updated.xml'

