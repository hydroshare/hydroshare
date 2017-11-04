from haystack.forms import FacetedSearchForm
from haystack.query import SQ, SearchQuerySet
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from django import forms

class DiscoveryForm(FacetedSearchForm):
    NElat = forms.CharField(widget = forms.HiddenInput(), required=False)
    NElng = forms.CharField(widget = forms.HiddenInput(), required=False)
    SWlat = forms.CharField(widget = forms.HiddenInput(), required=False)
    SWlng = forms.CharField(widget = forms.HiddenInput(), required=False)
    start_date = forms.DateField(label='From Date', required=False)
    end_date = forms.DateField(label='To Date', required=False)

    def search(self):
        if not self.cleaned_data.get('q'):
            sqs = self.searchqueryset.filter(discoverable=True).filter(is_replaced_by=False)
        else:
            sqs = self.searchqueryset.filter(text__startswith=self.cleaned_data.get('q'))\
                .filter(discoverable=True)\
                .filter(is_replaced_by=False)

        geo_sq = SQ()
        if self.cleaned_data['NElng'] and self.cleaned_data['SWlng']:
            if float(self.cleaned_data['NElng']) > float(self.cleaned_data['SWlng']):
		geo_sq = SQ(coverage_east__lte=float(self.cleaned_data['NElng']))
                geo_sq.add(SQ(coverage_east__gte=float(self.cleaned_data['SWlng'])), SQ.AND)
            else:
                geo_sq = SQ(coverage_east__gte=float(self.cleaned_data['SWlng']))
                geo_sq.add(SQ(coverage_east__lte=float(180)), SQ.OR)
                geo_sq.add(SQ(coverage_east__lte=float(self.cleaned_data['NElng'])), SQ.AND)
                geo_sq.add(SQ(coverage_east__gte=float(-180)), SQ.AND)

        if self.cleaned_data['NElat'] and self.cleaned_data['SWlat']:
            # latitude might be specified without longitude
            if geo_sq is None:
                geo_sq = SQ(coverage_north__lte=float(self.cleaned_data['NElat']))
            else:
                geo_sq.add(SQ(coverage_north__lte=float(self.cleaned_data['NElat'])), SQ.AND)
            geo_sq.add(SQ(coverage_north__gte=float(self.cleaned_data['SWlat'])), SQ.AND)

        if geo_sq:
            sqs = sqs.filter(geo_sq)


        # Check to see if a start_date was chosen.
        if self.cleaned_data['start_date']:
            sqs = sqs.filter(coverage_start_date__gte=self.cleaned_data['start_date'])

        # Check to see if an end_date was chosen.
        if self.cleaned_data['end_date']:
            sqs = sqs.filter(coverage_end_date__lte=self.cleaned_data['end_date'])

	authors_sq = None
        subjects_sq = None
        resource_type_sq = None
        public_sq = None
        owners_names_sq = None
        discoverable_sq = None
        published_sq = None
        variable_names_sq = None
        sample_mediums_sq = None
        units_names_sq = None

        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:

        for facet in self.selected_facets:
            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)

            if value:
                if "creators" in field:
                    author_sq.add(SQ(creators=sqs.query.clean(value)), SQ.OR)

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

                elif "published" in field:
                    published_sq.add(SQ(published=sqs.query.clean(value)), SQ.OR)

                elif 'variable_names' in field:
                    variable_sq.add(SQ(variable_names=sqs.query.clean(value)), SQ.OR)

                elif 'sample_mediums' in field:
                    sample_medium_sq.add(SQ(sample_mediums=sqs.query.clean(value)), SQ.OR)

                elif 'units_names' in field:
                    units_name_sq.add(SQ(units_names=sqs.query.clean(value)), SQ.OR)

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
        if owners_names_sq is not None:
            sqs = sqs.filter(owners_names_sq)
        if discoverable_sq is not None:
            sqs = sqs.filter(discoverable_sq)
        if published_sq:
            sqs = sqs.filter(published_sq)
        if variable_sq:
            sqs = sqs.filter(variable_sq)
        if sample_medium_sq:
            sqs = sqs.filter(sample_medium_sq)
        if units_name_sq:
            sqs = sqs.filter(units_name_sq)

        return sqs