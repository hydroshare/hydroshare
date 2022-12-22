import pytest
from django.test import Client


@pytest.mark.django_db
def test_citation_create(sample_user, resource_for_citation):
    """
    Citation CRUD
    """
    client = Client(enforce_csrf_checks=False)
    client.force_login(sample_user)
    # See metadata_element_pre_update_handler for assignment of POST data
    custom_citation = 'Creator(s) (Publication Year). Title, Version, Publisher, Resource Type, Identifier' \
                      ' (preferably encoded as a URL)'
    updated_citation = 'Updated Citation'
    client.post('/hsapi/_internal/{}/citation/add-metadata/'.format(resource_for_citation.short_id),
                data={'content': custom_citation}, HTTP_REFERER='http://url')
    # CREATE
    assert (str(resource_for_citation.metadata.citation.first()) == custom_citation)
    citation_id = resource_for_citation.metadata.citation.first().id
    client.post('/hsapi/_internal/{}/citation/{}/update-metadata/'.format(resource_for_citation.short_id,
                                                                          citation_id),
                data={'content': updated_citation}, HTTP_REFERER='http://url')
    # UPDATE
    assert (str(resource_for_citation.metadata.citation.first()) == updated_citation)
    client.post('/hsapi/_internal/{}/citation/{}/update-metadata/'.format(resource_for_citation.short_id,
                                                                          citation_id),
                data={'content': updated_citation}, HTTP_REFERER='http://url')
    # DELETE
    assert (str(resource_for_citation.metadata.citation.first()) == updated_citation)
    client.post('/hsapi/_internal/{}/citation/{}/delete-metadata/'.format(resource_for_citation.short_id,
                                                                          citation_id), HTTP_REFERER='http://url')
    assert (citation_id not in [citation.get('id') for citation in resource_for_citation.metadata.citation.all()])
