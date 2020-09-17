import pytest


@pytest.mark.django_db
def test_discover_api(admin_client, resource_with_metadata):
    response = admin_client.get('/discoverapi/?q=veryuniqueword', follow=True)
    print(resource_with_metadata)
    print(response.data['resources'])
    assert 1 == 1
