import requests
import pytest


@pytest.mark.django_db
def test_top_url(client):
    response = client.get('/')
    print(response.content)
    assert response.status_code == 200
