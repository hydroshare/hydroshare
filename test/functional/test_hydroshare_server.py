import pytest


@pytest.mark.django_db
def test_top_url(admin_client):
    response = admin_client.get('/collaborate/', follow=True)

    print(response.content)
    assert "My Groups" in response.content
