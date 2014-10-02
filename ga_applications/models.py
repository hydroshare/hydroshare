from django.contrib.gis.db import models
from mezzanine.pages.models import Page, RichText

class Application(Page, RichText):
    WMS = 0
    GOOGLE_ROADS = 1
    GOOGLE_HYBRID = 2
    GOOGLE_SATELLITE = 3
    OSM = 4
    BING_ROADS = 5
    BING_AERIAL = 6
    NONE = 10

    default_base_map = models.PositiveSmallIntegerField(choices=(
        (WMS, "Web Map Service"),
        (GOOGLE_ROADS, "Google Roads"),
        (GOOGLE_HYBRID, "Google Hybrid"),
        (GOOGLE_SATELLITE,"Google Satellite"),
        (OSM, "Open Streetmaps"),
        (BING_ROADS, "Bing Roads"),
        (BING_AERIAL, "Bing Aerial"),
        (NONE, "No Basemap"),
    ))

    script_tags = models.TextField(blank=True)
    link_tags = models.TextField(blank=True)
    application_script = models.FileField(upload_to="applications", null=True, blank=True)
    application_css = models.FileField(upload_to="applications", null=True, blank=True)
    left_sidebar_html = models.TextField(blank=True, null=True)
    right_sidebar_html = models.TextField(blank=True, null=True)
    left_sidebar_columns = models.IntegerField(default=0)
    right_sidebar_columns = models.IntegerField(default=0)
    header_html = models.TextField(blank=True, null=True)
    footer_html = models.TextField(blank=True, null=True)
    renderedlayers = models.ManyToManyField(through="ApplicationLayer", blank=True, to='ga_resources.RenderedLayer')
    default_includes = models.BooleanField(default=True)

    @property
    def remainder(self):
        return 12 - (self.left_sidebar_columns + self.right_sidebar_columns)

class ApplicationLayer(models.Model):
    application = models.ForeignKey(Application)
    renderedlayer = models.ForeignKey("ga_resources.RenderedLayer")
    weight = models.IntegerField(default=0)

    class Meta:
        ordering = ("-weight",)
