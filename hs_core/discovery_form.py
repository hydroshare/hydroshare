from haystack.forms import FacetedSearchForm
from haystack.query import SQ
from django import forms
from hs_core.discovery_parser import ParseSQ, NoMatchingBracketsFound, UnhandledException, \
    FieldNotKnownException

FACETED_FIELDS = ['author', 'contributor', 'owner', 'resource_type',
                  'subject', 'variable', 'sample_medium', 'availability']


class DiscoveryForm(FacetedSearchForm):
    SORT_ORDER_VALUES = ('title', 'author', 'created', 'modified')
    SORT_ORDER_CHOICES = (('title', 'Title'),
                          ('author', 'First Author'),
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
        sqs = self.searchqueryset.all().filter(replaced=False)
        if self.cleaned_data.get('q'):
            # This corrects for an failed match of complete words, as documented in issue #2308.
            # The text__startswith=cdata matches stemmed words in documents with an unstemmed cdata.
            # The text=cdata matches stemmed words after stemming cdata as well.
            # The stem of "Industrial", according to the aggressive default stemmer, is "industri".
            # Thus "Industrial" does not match "Industrial" in the document according to
            # startswith, but does match according to text=cdata.
            cdata = self.cleaned_data.get('q')
            # error = None
            try:
                parser = ParseSQ()
                parsed = parser.parse(cdata)
                sqs = sqs.filter(parsed)
            except UnhandledException:  # as e:
                sqs = self.searchqueryset.none()
                # error = "syntax error: {}".format(e.value)
            except NoMatchingBracketsFound:  # as e:
                sqs = self.searchqueryset.none()
                # error = e.value
            except FieldNotKnownException:  # as e:
                sqs = self.searchqueryset.none()
                # error = e.value

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
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']

        # allow overlapping ranges
        # cs < s < ce OR s < cs => s < ce
        # AND
        # cs < e < ce OR e > ce => cs < e
        if start_date and end_date:
            sqs = sqs.add(SQ(coverage_end_date__gte=start_date) &
                          SQ(coverage_start_date__lte=end_date))
        elif start_date:
            sqs = sqs.add(SQ(coverage_end_date__gte=start_date))
        elif end_date:
            sqs = sqs.add(SQ(coverage_start_date__lte=end_date))

        # Check to see if an end_date was chosen.
        if self.cleaned_data['end_date']:
            sqs = sqs.filter(coverage_end_date__lte=self.cleaned_data['end_date'])

        if self.cleaned_data['coverage_type']:
            sqs = sqs.filter(coverage_types__in=[self.cleaned_data['coverage_type']])

        author_sq = None
        creator_sq = None
        owner_sq = None
        subject_sq = None
        resource_type_sq = None
        accessibility_sq = None
        variable_sq = None
        sample_medium_sq = None
        units_sq = None

        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:

        for facet in self.selected_facets:
            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)
            value = sqs.query.clean(value)

            if value:
                if "author" in field:
                    if author_sq is None:
                        author_sq = SQ(author=value)
                    else:
                        author_sq.add(SQ(author=value), SQ.OR)

                if "creator" in field:
                    if creator_sq is None:
                        creator_sq = SQ(creator=value)
                    else:
                        creator_sq.add(SQ(creator=value), SQ.OR)

                elif "owner" in field:
                    if owner_sq is None:
                        owner_sq = SQ(owner=value)
                    else:
                        owner_sq.add(SQ(owner=value), SQ.OR)

                elif "subject" in field:
                    if subject_sq is None:
                        subject_sq = SQ(subject=value)
                    else:
                        subject_sq.add(SQ(subject=value), SQ.OR)

                elif "resource_type" in field:
                    if resource_type_sq is None:
                        resource_type_sq = SQ(resource_type=value)
                    else:
                        resource_type_sq.add(SQ(resource_type=value), SQ.OR)

                elif "accessibility" in field:
                    if accessibility_sq is None:
                        accessibility_sq = SQ(accessibility=value)
                    else:
                        accessibility_sq.add(SQ(accessibility=value), SQ.OR)

                elif 'variable' in field:
                    if variable_sq is None:
                        variable_sq = SQ(variable=value)
                    else:
                        variable_sq.add(SQ(variable=value), SQ.OR)

                elif 'sample_medium' in field:
                    if sample_medium_sq is None:
                        sample_medium_sq = SQ(sample_medium=value)
                    else:
                        sample_medium_sq.add(SQ(sample_medium=value), SQ.OR)

                elif 'units' in field:
                    if units_sq is None:
                        units_sq = SQ(units=value)
                    else:
                        units_sq.add(SQ(units=value), SQ.OR)

                else:
                    continue

        if author_sq is not None:
            sqs = sqs.filter(author_sq)
        if creator_sq is not None:
            sqs = sqs.filter(creator_sq)
        if owner_sq is not None:
            sqs = sqs.filter(owner_sq)
        if subject_sq is not None:
            sqs = sqs.filter(subject_sq)
        if resource_type_sq is not None:
            sqs = sqs.filter(resource_type_sq)
        if accessibility_sq is not None:
            sqs = sqs.filter(accessibility_sq)
        if variable_sq is not None:
            sqs = sqs.filter(variable_sq)
        if sample_medium_sq is not None:
            sqs = sqs.filter(sample_medium_sq)
        if units_sq is not None:
            sqs = sqs.filter(units_sq)

        return sqs
