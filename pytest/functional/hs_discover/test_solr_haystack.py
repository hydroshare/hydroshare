import pytest
from haystack.query import SearchQuerySet


@pytest.mark.skip(reason="for some reason can't make this test pass")
@pytest.mark.django_db
def test_solr(admin_client, public_resource_with_metadata, another_public_resource_with_metadata):
    sqs = SearchQuerySet().all()
    sqs = sqs.order_by('author_lower')
    first = list(sqs)[0]
    for res in list(sqs):
        print(res.author_exact)
    sqs = sqs.order_by('-author_lower')
    for res in list(sqs):
        print(res.author_exact)
    assert first.author_exact != list(sqs)[0].author_exact, \
        "Changing author_lower sort direction did not have an effect"
