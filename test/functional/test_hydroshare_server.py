import pytest


@pytest.mark.django_db
def test_my_resources_page(admin_client, resource_with_metadata):
    """Resource with unique id is found on my resources page"""
    response = admin_client.get('/my-resources/', follow=True)
    assert resource_with_metadata in response.content
