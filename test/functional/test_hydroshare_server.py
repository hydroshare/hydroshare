import pytest


@pytest.mark.django_db
def test_top_url(client):
    response = client.get('tests/')
    print(response.content)
    assert response.status_code == 200

# TODO figure out how to get the test url to work     url(r"^tests/$", direct_to_template, {"template": "index.html"}, name="tests")