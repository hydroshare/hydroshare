import json

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase


class TestUniversities(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_universities_no_query(self):
        response = self.client.get('/hsapi/dictionary/universities/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 9363)

    def test_universities_query(self):
        response = self.client.get('/hsapi/dictionary/universities/dubai/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(len(content), 9)
