from django import forms
from haystack.forms import FacetedSearchForm
from haystack.query import SQ, SearchQuerySet
from crispy_forms.layout import *
from crispy_forms.bootstrap import *


class DiscoveryForm(FacetedSearchForm):
    def search(self):
        sqs = super(FacetedSearchForm, self).search().filter(discoverable=True)
        author_sq = SQ()
        subjects_sq = SQ()
        resource_sq = SQ()
        public_sq = SQ()
        owner_sq = SQ()
        discoverable_sq = SQ()
        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:

        for facet in self.selected_facets:
            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)

            if value:
                if "author" in field:
                    author_sq.add(SQ(author=sqs.query.clean(value)), SQ.OR)

                elif "subjects" in field:
                    subjects_sq.add(SQ(subjects=sqs.query.clean(value)), SQ.OR)

                elif "resource_type" in field:
                    resource_sq.add(SQ(resource_type=sqs.query.clean(value)), SQ.OR)

                elif "public" in field:
                    public_sq.add(SQ(public=sqs.query.clean(value)), SQ.OR)

                elif "owners_names" in field:
                    owner_sq.add(SQ(owners_names=sqs.query.clean(value)), SQ.OR)

                elif "discoverable" in field:
                    discoverable_sq.add(SQ(discoverable=sqs.query.clean(value)), SQ.OR)

                else:
                    continue

        if author_sq:
            sqs = sqs.filter(author_sq)
        if subjects_sq:
            sqs = sqs.filter(subjects_sq)
        if resource_sq:
            sqs = sqs.filter(resource_sq)
        if public_sq:
            sqs = sqs.filter(public_sq)
        if owner_sq:
            sqs = sqs.filter(owner_sq)
        if discoverable_sq:
            sqs = sqs.filter(discoverable_sq)
        return sqs