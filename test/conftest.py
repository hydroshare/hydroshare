import pytest


@pytest.fixture(scope="session")
def test_top_url(client):
    response = client.get('/')
    assert response.status_code == 200
