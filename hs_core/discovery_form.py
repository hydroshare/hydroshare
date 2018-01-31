from haystack.forms import FacetedSearchForm
from haystack.query import SQ
from django import forms
from hs_core.discovery_parser import ParseSQ, MatchingBracketsNotFoundError, \
    FieldNotRecognizedError, InequalityNotAllowedError, MalformedDateError

FACETED_FIELDS = ['creator', 'contributor', 'owner', 'resource_type', 'subject', 'availability']


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
        self.parse_error = None  # error return from parser
        sqs = self.searchqueryset.all().filter(replaced=False)
        if self.cleaned_data.get('q'):
            # The prior code corrected for an failed match of complete words, as documented
            # in issue #2308. This version instead uses an advanced query syntax in which
            # "word" indicates an exact match and the bare word indicates a stemmed match.
            cdata = self.cleaned_data.get('q')
            try:
                parser = ParseSQ()
                parsed = parser.parse(cdata)
                sqs = sqs.filter(parsed)
            except ValueError as e:
                sqs = self.searchqueryset.none()
                self.parse_error = "Value error: {}. No matches. Please try again".format(e.value)
                return sqs
            except MatchingBracketsNotFoundError as e:
                sqs = self.searchqueryset.none()
                self.parse_error = "{} No matches. Please try again.".format(e.value)
                return sqs
            except MalformedDateError as e:
                sqs = self.searchqueryset.none()
                self.parse_error = "{} No matches. Please try again.".format(e.value)
                return sqs
            except FieldNotRecognizedError as e:
                sqs = self.searchqueryset.none()
                self.parse_error = \
                    ("{} Field delimiters include title, contributor, subject, etc. " +
                     "Please try again.")\
                    .format(e.value)
                return sqs
            except InequalityNotAllowedError as e:
                sqs = self.searchqueryset.none()
                self.parse_error = "{} No matches. Please try again.".format(e.value)
                return sqs

        geo_sq = None
        if self.cleaned_data['NElng'] and self.cleaned_data['SWlng']:
            if float(self.cleaned_data['NElng']) > float(self.cleaned_data['SWlng']):
                geo_sq = SQ(east__lte=float(self.cleaned_data['NElng']))
                geo_sq.add(SQ(east__gte=float(self.cleaned_data['SWlng'])), SQ.AND)
            else:
                geo_sq = SQ(east__gte=float(self.cleaned_data['SWlng']))
                geo_sq.add(SQ(east__lte=float(180)), SQ.OR)
                geo_sq.add(SQ(east__lte=float(self.cleaned_data['NElng'])), SQ.AND)
                geo_sq.add(SQ(east__gte=float(-180)), SQ.AND)

        if self.cleaned_data['NElat'] and self.cleaned_data['SWlat']:
            # latitude might be specified without longitude
            if geo_sq is None:
                geo_sq = SQ(north__lte=float(self.cleaned_data['NElat']))
            else:
                geo_sq.add(SQ(north__lte=float(self.cleaned_data['NElat'])), SQ.AND)
            geo_sq.add(SQ(north__gte=float(self.cleaned_data['SWlat'])), SQ.AND)

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
            sqs = sqs.filter(SQ(end_date__gte=start_date) &
                             SQ(start_date__lte=end_date))
        elif start_date:
            sqs = sqs.filter(SQ(end_date__gte=start_date))

        elif end_date:
            sqs = sqs.filter(SQ(start_date__lte=end_date))

        if self.cleaned_data['coverage_type']:
            sqs = sqs.filter(coverage_types__in=[self.cleaned_data['coverage_type']])

        creator_sq = None
        contributor_sq = None
        owner_sq = None
        subject_sq = None
        resource_type_sq = None
        availability_sq = None

        # spammed facets eliminated due to poor metadata quality
        # variable_sq = None
        # sample_medium_sq = None

        # We need to process each facet to ensure that the field name and the
        # value are quoted correctly and separately:

        for facet in self.selected_facets:
            if ":" not in facet:
                continue

            field, value = facet.split(":", 1)
            value = sqs.query.clean(value)

            if value:
                if "creator" in field:
                    if creator_sq is None:
                        creator_sq = SQ(creator=value)
                    else:
                        creator_sq.add(SQ(creator=value), SQ.OR)

                if "contributor" in field:
                    if contributor_sq is None:
                        contributor_sq = SQ(contributor=value)
                    else:
                        contributor_sq.add(SQ(contributor=value), SQ.OR)

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

                elif "availability" in field:
                    if availability_sq is None:
                        availability_sq = SQ(availability=value)
                    else:
                        availability_sq.add(SQ(availability=value), SQ.OR)

                # spammed facets eliminated due to poor metadata quality

                # elif 'variable' in field:
                #     if variable_sq is None:
                #         variable_sq = SQ(variable=value)
                #     else:
                #         variable_sq.add(SQ(variable=value), SQ.OR)

                # elif 'sample_medium' in field:
                #     if sample_medium_sq is None:
                #         sample_medium_sq = SQ(sample_medium=value)
                #     else:
                #         sample_medium_sq.add(SQ(sample_medium=value), SQ.OR)

                else:
                    continue

        if creator_sq is not None:
            sqs = sqs.filter(creator_sq)
        if contributor_sq is not None:
            sqs = sqs.filter(contributor_sq)
        if owner_sq is not None:
            sqs = sqs.filter(owner_sq)
        if subject_sq is not None:
            sqs = sqs.filter(subject_sq)
        if resource_type_sq is not None:
            sqs = sqs.filter(resource_type_sq)
        if availability_sq is not None:
            sqs = sqs.filter(availability_sq)

        # spammed facets eliminated due to poor metadata quality

        # if variable_sq is not None:
        #     sqs = sqs.filter(variable_sq)
        # if sample_medium_sq is not None:
        #     sqs = sqs.filter(sample_medium_sq)

        return sqs
