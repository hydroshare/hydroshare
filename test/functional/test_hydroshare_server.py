import pytest


@pytest.mark.django_db
def test_top_url(admin_client):
    response = admin_client.get('/search/', follow=True)

    print(response.content)
    assert "Discover" in response.content
