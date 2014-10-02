import datetime

from django.db.models.signals import post_save, pre_delete, pre_save
from django.conf import settings as s
from django.utils.timezone import utc
from . import tasks, dispatch, drivers
from .models import DataResource, Style, RenderedLayer
import os


def dataresource_pre_save(sender, instance, *args, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        instance.last_refresh = instance.last_refresh or datetime.datetime.utcnow().replace(tzinfo=utc)
        if instance.refresh_every:
            instance.next_refresh = instance.last_refresh + instance.refresh_every


def dataresource_post_save(sender, instance, *args, **kwargs):
    if not instance.native_srs:
        if instance.big:
            tasks.data_resource_compute_fields.delay(instance.pk)
        else:
            instance.driver_instance.compute_fields()


def purge_cache_on_delete(sender, instance, *args, **kwargs):
    if sender is DataResource:
        instance.resource.clear_cache()
        if instance.resource_file and os.path.exists(os.path.join(s.MEDIA_ROOT, instance.resource_file.name)):
            os.unlink(os.path.join(s.MEDIA_ROOT, instance.resource_file.name))
    elif sender is Style:
        for layer in instance.renderedlayer_set.all():
            layer.resource.clear_cache()
    elif sender is RenderedLayer:
        layer.resource.clear_cache()


def purge_resource_data(sender, instance, *args, **kwargs):
    if sender is DataResource:
        instance.driver_instance.clear_cache()


def shave_tile_caches(sender, instance, bbox, *args, **kwargs):
    drivers.CacheManager.get().shave_caches(instance, bbox)


def trim_tile_caches(sender, instance, *args, **kwargs):
    if sender is Style:
        drivers.CacheManager.get().remove_caches_for_style(instance)
    elif sender is DataResource:
        drivers.CacheManager.get().remove_caches_for_resource(instance)
    elif sender is RenderedLayer:
        drivers.CacheManager.get().remove_caches_for_layer(instance)


pre_save.connect(dataresource_pre_save, sender=DataResource, weak=False)
post_save.connect(dataresource_post_save, sender=DataResource, weak=False)
pre_delete.connect(purge_cache_on_delete, sender=Style, weak=False)
pre_delete.connect(purge_cache_on_delete, sender=DataResource, weak=False)
pre_delete.connect(purge_resource_data, sender=DataResource, weak=False)

dispatch.features_updated.connect(shave_tile_caches, weak=False)
dispatch.features_created.connect(shave_tile_caches, weak=False)
dispatch.features_deleted.connect(shave_tile_caches, weak=False)
post_save.connect(trim_tile_caches, sender=Style, weak=False)
pre_delete.connect(trim_tile_caches, sender=DataResource, weak=False)
pre_delete.connect(trim_tile_caches, sender=Style, weak=False)
pre_delete.connect(trim_tile_caches, sender=RenderedLayer, weak=False)
