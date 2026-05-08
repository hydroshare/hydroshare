from django import forms


CONTENT_TYPE_CHOICES = [
    ("ToolResource", "App Connector"),
    ("CollectionResource", "Collection"),
    ("CSVLogicalFile", "CSV Data"),
    ("FileSetLogicalFile", "File Set Generic Data"),
    ("GeoFeatureLogicalFile", "Geographic Feature (ESRI Shapefiles)"),
    ("GeographicFeatureAggregation", "Geographic Feature (ESRI Shapefiles)"),
    ("GeoRasterLogicalFile", "Geographic Raster"),
    ("GeographicRasterAggregation", "Geographic Raster"),
    ("ModelInstanceLogicalFile", "Model Instance"),
    ("ModelProgramLogicalFile", "Model Program"),
    ("NetCDFLogicalFile", "Multidimensional (NetCDF)"),
    ("MultidimensionalAggregation", "Multidimensional (NetCDF)"),
    ("RefTimeseriesLogicalFile", "Reference to Time Series"),
    ("CompositeResource", "Resource"),
    ("GenericLogicalFile", "Single File Generic Data"),
    ("TimeSeriesLogicalFile", "Time Series"),
    ("TimeSeriesAggregation", "Time Series"),
]

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
    contentType = forms.MultipleChoiceField(required=False, choices=CONTENT_TYPE_CHOICES)
    creativeWorkStatus = forms.MultipleChoiceField(required=False, choices=STATUS_CHOICES)
    creatorName = forms.CharField(required=False)
    keyword = forms.CharField(required=False)
    fundingFunderName = forms.CharField(required=False)
    dataCoverageStart = forms.IntegerField(required=False, min_value=1900, max_value=2100)
    dataCoverageEnd = forms.IntegerField(required=False, min_value=1900, max_value=2100)
    dateCreatedStart = forms.IntegerField(required=False, min_value=1900, max_value=2100)
    dateCreatedEnd = forms.IntegerField(required=False, min_value=1900, max_value=2100)
    publishedStart = forms.IntegerField(required=False, min_value=1900, max_value=2100)
    publishedEnd = forms.IntegerField(required=False, min_value=1900, max_value=2100)
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
