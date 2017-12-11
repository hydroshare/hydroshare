from haystack.forms import FacetedSearchForm
from haystack.query import SQ
from django import forms


class DiscoveryForm(FacetedSearchForm):
    SORT_ORDER_VALUES = ('title', 'author_normalized', 'created', 'modified')
    SORT_ORDER_CHOICES = (('title', 'Title'),
                          ('author_normalized', 'First Author'),
                          ('created', 'Date Created'),
                          ('modified', 'Last Modified'))

    SORT_DIRECTION_VALUES = ('', '-')
    SORT_DIRECTION_CHOICES = (('', 'Ascending'),
                              ('-', 'Descending'))

    NElat = forms.CharField(widget=forms.HiddenInput(), required=False)
    NElng = forms.CharField(widget=forms.HiddenInput(), required=False)
    SWlat = forms.CharField(widget=forms.HiddenInput(), required=False)
    SWlng = forms.CharField(widget=forms.HiddenInput(), required=False)
    start_date = forms.DateField(label='From Date', required=False)
    end_date = forms.DateField(label='To Date', required=False)
    coverage_type = forms.CharField(widget=forms.HiddenInput(), required=False)
    sort_order = forms.CharField(label='Sort By:',
                                 widget=forms.Select(choices=SORT_ORDER_CHOICES),
                                 required=False)
    sort_direction = forms.CharField(label='Sort Direction:',
                                     widget=forms.Select(choices=SORT_DIRECTION_CHOICES),
                                     required=False)

    def search(self):
        if not self.cleaned_data.get('q'):
            sqs = self.searchqueryset.all().filter(is_replaced_by=False)
        else:
            # This corrects for an failed match of complete words, as documented in issue #2308.
            # The text__startswith=cdata matches stemmed words in documents with an unstemmed cdata.
            # The text=cdata matches stemmed words after stemming cdata as well.
            # The stem of "Industrial", according to the aggressive default stemmer, is "industri".
            # Thus "Industrial" does not match "Industrial" in the document according to
            # startswith, but does match according to text=cdata.
            cdata = self.cleaned_data.get('q')
            sqs = self.searchqueryset.all()\
                .filter(SQ(text__startswith=cdata) | SQ(text=cdata))\
                .filter(is_replaced_by=False)

        geo_sq = None
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

        if geo_sq is not None:
            sqs = sqs.filter(geo_sq)

        # Check to see if a start_date was chosen.
        if self.cleaned_data['start_date']:
            sqs = sqs.filter(coverage_start_date__gte=self.cleaned_data['start_date'])

        # Check to see if an end_date was chosen.
        if self.cleaned_data['end_date']:
            sqs = sqs.filter(coverage_end_date__lte=self.cleaned_data['end_date'])

        if self.cleaned_data['coverage_type']:
            sqs = sqs.filter(coverage_types__in=[self.cleaned_data['coverage_type']])

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
            value = sqs.query.clean(value)

            if value:
                if "creators" in field:
                    if authors_sq is None:
                        authors_sq = SQ(creators=value)
                    else:
                        authors_sq.add(SQ(creators=value), SQ.OR)

                elif "subjects" in field:
                    if subjects_sq is None:
                        subjects_sq = SQ(subjects=value)
                    else:
                        subjects_sq.add(SQ(subjects=value), SQ.OR)

                elif "resource_type" in field:
                    if resource_type_sq is None:
                        resource_type_sq = SQ(resource_type=value)
                    else:
                        resource_type_sq.add(SQ(resource_type=value), SQ.OR)

                elif "public" in field:
                    if public_sq is None:
                        public_sq = SQ(public=value)
                    else:
                        public_sq.add(SQ(public=value), SQ.OR)

                elif "owners_names" in field:
                    if owners_names_sq is None:
                        owners_names_sq = SQ(owners_names=value)
                    else:
                        owners_names_sq.add(SQ(owners_names=value), SQ.OR)

                elif "discoverable" in field:
                    if discoverable_sq is None:
                        discoverable_sq = SQ(discoverable=value)
                    else:
                        discoverable_sq.add(SQ(discoverable=value), SQ.OR)

                elif "published" in field:
                    if published_sq is None:
                        published_sq = SQ(published=value)
                    else:
                        published_sq.add(SQ(published=value), SQ.OR)

                elif 'variable_names' in field:
                    if variable_names_sq is None:
                        variable_names_sq = SQ(variable_names=value)
                    else:
                        variable_names_sq.add(SQ(variable_names=value), SQ.OR)

                elif 'sample_mediums' in field:
                    if sample_mediums_sq is None:
                        sample_mediums_sq = SQ(sample_mediums=value)
                    else:
                        sample_mediums_sq.add(SQ(sample_mediums=value), SQ.OR)

                elif 'units_names' in field:
                    if units_names_sq is None:
                        units_names_sq = SQ(units_names=value)
                    else:
                        units_names_sq.add(SQ(units_names=value), SQ.OR)

                else:
                    continue

        if authors_sq is not None:
            sqs = sqs.filter(authors_sq)
        if subjects_sq is not None:
            sqs = sqs.filter(subjects_sq)
        if resource_type_sq is not None:
            sqs = sqs.filter(resource_type_sq)
        if public_sq is not None:
            sqs = sqs.filter(public_sq)
        if owners_names_sq is not None:
            sqs = sqs.filter(owners_names_sq)
        if discoverable_sq is not None:
            sqs = sqs.filter(discoverable_sq)
        if published_sq is not None:
            sqs = sqs.filter(published_sq)
        if variable_names_sq is not None:
            sqs = sqs.filter(variable_names_sq)
        if sample_mediums_sq is not None:
            sqs = sqs.filter(sample_mediums_sq)
        if units_names_sq is not None:
            sqs = sqs.filter(units_names_sq)

        return sqs
