from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import Group
from django.db import close_old_connections, transaction
from django.test import TransactionTestCase

from hs_core import hydroshare, models
from hs_core.hydroshare.resource import get_data_zone_usage
from hs_core.models import BaseResource, ResourceFile, ResourceSizeCache


class ResourceSizeCacheConcurrencyTest(TransactionTestCase):
    def test_writer_invalidates_a_concurrent_refresh(self):
        Group.objects.get_or_create(name='Hydroshare Author')
        user = hydroshare.create_account(
            'cache-test@example.com', username='cache' + uuid4().hex,
            first_name='Cache', last_name='Test', groups=[],
        )
        resource = hydroshare.create_resource('CompositeResource', user, 'Cache test')
        with patch.object(ResourceFile, 'calculate_size'):
            resource_file = ResourceFile.objects.create(
                content_object=resource, resource_file='concurrent-cache-test', _size=10,
            )
        self.addCleanup(user.delete)
        self.addCleanup(resource.delete)
        self.addCleanup(lambda: ResourceFile.objects.filter(pk=resource_file.pk).delete())

        writer_ready = Event()
        invalidate = models.invalidate_resource_size_cache

        def notify_then_invalidate(resource_ids, using):
            writer_ready.set()
            return invalidate(resource_ids, using)

        def update_file():
            close_old_connections()
            try:
                ResourceFile.objects.filter(pk=resource_file.pk).update(_size=30)
            finally:
                close_old_connections()

        with patch('hs_core.models.invalidate_resource_size_cache', side_effect=notify_then_invalidate):
            with ThreadPoolExecutor(max_workers=1) as executor:
                with transaction.atomic():
                    BaseResource.objects.select_for_update().get(pk=resource.pk)
                    future = executor.submit(update_file)
                    self.assertTrue(writer_ready.wait(timeout=10))
                    self.assertEqual(resource.get_size_cache().size, 10)
                future.result(timeout=10)

        self.assertFalse(ResourceSizeCache.objects.filter(resource=resource).exists())
        self.assertEqual(get_data_zone_usage(user.username), 30)
