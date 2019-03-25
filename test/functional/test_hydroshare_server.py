import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_discover_page(resource_with_metadata):
    """Resource with unique id is found on my resources page"""
    client = APIClient()
    client.login(username='testuser', password='foobar')

    response = client.get('/my-resources/', follow=True)
    assert resource_with_metadata in response.content
