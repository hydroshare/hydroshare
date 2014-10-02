from django.dispatch import Signal

dataset_created = Signal(providing_args=[])
dataset_deleted = Signal(providing_args=[])
dataset_column_added = Signal(providing_args=[])
features_created = Signal(providing_args=[])
features_updated = Signal(providing_args=[])
features_deleted = Signal(providing_args=[])
features_retrieved = Signal(providing_args=['feature_count'])
tile_rendered = Signal(providing_args=[])
wms_rendered = Signal(providing_args=[])
wfs_rendered = Signal(providing_args=['feature_count'])
api_accessed = Signal(providing_args=['user', 'call'])