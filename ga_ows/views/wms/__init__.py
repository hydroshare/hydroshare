from ga_ows.views.wms.base import WMS, WMSAdapterBase

__all__ = [WMS, WMSAdapterBase]

try:
    from ga_ows.views.wms.geodjango import GeoDjangoWMSAdapter
    __all__.append(GeoDjangoWMSAdapter)
except ImportError:
    pass

try:
    from ga_ows.views.wms.ogr import OGRDatasetWMSAdapter
    __all__.append(OGRDatasetWMSAdapter)
except ImportError:
    pass
