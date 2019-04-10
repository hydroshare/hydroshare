import pytest


@pytest.mark.django_db
def test_search_url(admin_client):
    response = admin_client.get('/search/', follow=True)
    assert "Discover" in response.content
