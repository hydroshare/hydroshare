import pytest
import uuid


@pytest.mark.django_db
def test_citation_create(admin_client, resource_for_citation):
    """
    Add a unique citation to a resource
    """
    citation = str(uuid.uuid4())
    resource_for_citation.citation = citation
    # base_sample_resource.raccess.save()
    # base_sample_resource.save()
    assert resource_for_citation.citation == citation
