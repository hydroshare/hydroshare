import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_discover_page(resource_with_metadata):
    client = APIClient()
    client.login(username='testuser', password='foobar')

    response = client.get('/my-resources/', follow=True)
    assert "d49aebb3-4e64-4732-8ff2-5c43617effee" in response.content
