import csv
import json

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import University


class TestUniversities(APITestCase):
    def setUp(self):
        self.client = APIClient()
        world_universities_csv_file_path = "hs_dictionary/migrations/world-universities.csv"
        University.objects.all().delete()
        with open(world_universities_csv_file_path) as f:
            reader = csv.reader(f)
            for i, line in enumerate(reader):
                University.objects.create(
                    name=line[1],
                    country_code=line[0],
                    url=line[2]
                )

    def tearDown(self):
        super(TestUniversities, self).tearDown()
        University.objects.all().delete()

    def test_universities_no_query(self):
        response = self.client.get('/hsapi/dictionary/universities/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content.decode())
        self.assertEqual(len(content), 1)

    def test_universities_query(self):
        response = self.client.get('/hsapi/dictionary/universities/?term=dubai', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content.decode())
        self.assertEqual(len(content), 9)
