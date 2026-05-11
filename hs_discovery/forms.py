from datetime import date

from django import forms


CURRENT_YEAR = date.today().year
TEMPORAL_MIN_YEAR = 2010
DISCOVERY_MIN_YEAR = 2010


CONTENT_TYPE_FILTERS = [
    ("tool-resource", "App Connector", ["ToolResource"]),
    ("collection-resource", "Collection", ["CollectionResource"]),
    ("csv-logical-file", "CSV Data", ["CSVLogicalFile"]),
    ("fileset-logical-file", "File Set Generic Data", ["FileSetLogicalFile"]),
    (
        "geographic-feature",
        "Geographic Feature (ESRI Shapefiles)",
        ["GeoFeatureLogicalFile", "GeographicFeatureAggregation"],
    ),
    (
        "geographic-raster",
        "Geographic Raster",
        ["GeoRasterLogicalFile", "GeographicRasterAggregation"],
    ),
    ("model-instance", "Model Instance", ["ModelInstanceLogicalFile"]),
    ("model-program", "Model Program", ["ModelProgramLogicalFile"]),
    (
        "multidimensional",
        "Multidimensional (NetCDF)",
        ["NetCDFLogicalFile", "MultidimensionalAggregation"],
    ),
    ("reference-timeseries", "Reference to Time Series", ["RefTimeseriesLogicalFile"]),
    ("resource", "Resource", ["CompositeResource"]),
    ("generic-logical-file", "Single File Generic Data", ["GenericLogicalFile"]),
    (
        "time-series",
        "Time Series",
        ["TimeSeriesLogicalFile", "TimeSeriesAggregation"],
    ),
]

CONTENT_TYPE_CHOICES = [(key, label) for key, label, _values in CONTENT_TYPE_FILTERS]
CONTENT_TYPE_VALUE_MAP = {key: values for key, _label, values in CONTENT_TYPE_FILTERS}

STATUS_CHOICES = [
    ("Discoverable", "Discoverable"),
    ("Public", "Public"),
    ("Published", "Published"),
]

SORT_CHOICES = [
    ("relevance", "Relevance"),
    ("most-viewed", "Most Viewed"),
    ("title", "Title"),
    ("first-author", "First Author"),
    ("date-created", "Date Created"),
    ("last-modified", "Last Modified"),
]

ORDER_CHOICES = [
    ("asc", "Ascending"),
    ("desc", "Descending"),
]


class DiscoverySearchForm(forms.Form):
    term = forms.CharField(required=False)
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES, initial="relevance")
    order = forms.ChoiceField(required=False, choices=ORDER_CHOICES)
    enableContentType = forms.BooleanField(required=False)
    enableAvailability = forms.BooleanField(required=False)
    enableDataCoverage = forms.BooleanField(required=False)
    enableDateCreated = forms.BooleanField(required=False)
    enablePublished = forms.BooleanField(required=False)
    contentType = forms.MultipleChoiceField(required=False, choices=CONTENT_TYPE_CHOICES)
    creativeWorkStatus = forms.MultipleChoiceField(required=False, choices=STATUS_CHOICES)
    creatorName = forms.CharField(required=False)
    keyword = forms.CharField(required=False)
    fundingFunderName = forms.CharField(required=False)
    dataCoverageStart = forms.IntegerField(required=False, min_value=TEMPORAL_MIN_YEAR, max_value=CURRENT_YEAR)
    dataCoverageEnd = forms.IntegerField(required=False, min_value=TEMPORAL_MIN_YEAR, max_value=CURRENT_YEAR)
    dateCreatedStart = forms.IntegerField(required=False, min_value=DISCOVERY_MIN_YEAR, max_value=CURRENT_YEAR)
    dateCreatedEnd = forms.IntegerField(required=False, min_value=DISCOVERY_MIN_YEAR, max_value=CURRENT_YEAR)
    publishedStart = forms.IntegerField(required=False, min_value=DISCOVERY_MIN_YEAR, max_value=CURRENT_YEAR)
    publishedEnd = forms.IntegerField(required=False, min_value=DISCOVERY_MIN_YEAR, max_value=CURRENT_YEAR)
    pageSize = forms.IntegerField(required=False, initial=20, min_value=1)
    paginationToken = forms.CharField(required=False)

    def clean_term(self):
        return (self.cleaned_data.get("term") or "").strip()

    def clean_sort(self):
        return self.cleaned_data.get("sort") or "relevance"

    def clean_order(self):
        return self.cleaned_data.get("order") or None

    def clean_creatorName(self):
        return (self.cleaned_data.get("creatorName") or "").strip()

    def clean_keyword(self):
        return (self.cleaned_data.get("keyword") or "").strip()

    def clean_fundingFunderName(self):
        return (self.cleaned_data.get("fundingFunderName") or "").strip()

    def clean_dataCoverageStart(self):
        return self.cleaned_data.get("dataCoverageStart") or None

    def clean_dataCoverageEnd(self):
        return self.cleaned_data.get("dataCoverageEnd") or None

    def clean_dateCreatedStart(self):
        return self.cleaned_data.get("dateCreatedStart") or None

    def clean_dateCreatedEnd(self):
        return self.cleaned_data.get("dateCreatedEnd") or None

    def clean_publishedStart(self):
        return self.cleaned_data.get("publishedStart") or None

    def clean_publishedEnd(self):
        return self.cleaned_data.get("publishedEnd") or None

    def clean_pageSize(self):
        return self.cleaned_data.get("pageSize") or 20

    def clean_enableContentType(self):
        return bool(self.cleaned_data.get("enableContentType"))

    def clean_enableAvailability(self):
        return bool(self.cleaned_data.get("enableAvailability"))

    def clean_enableDataCoverage(self):
        return bool(self.cleaned_data.get("enableDataCoverage"))

    def clean_enableDateCreated(self):
        return bool(self.cleaned_data.get("enableDateCreated"))

    def clean_enablePublished(self):
        return bool(self.cleaned_data.get("enablePublished"))
