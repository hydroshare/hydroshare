import pytest


@pytest.mark.django_db
def test_discover_api(admin_client):
    response = admin_client.get('/discoverapi/', follow=True)
    print(response.data['resources'])
    assert 1==1
