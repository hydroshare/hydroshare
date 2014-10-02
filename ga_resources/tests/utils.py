from django.core.files import File
from ga_resources import models

# load a test dataset using the SQLite driver
def load_example_dataset_from_filesystem():
    ds = models.DataResource.objects.create(
        title='Test Resource',
        driver='ga_resources.drivers.spatialite',
        resource_file=File(open('ga_resources/tests/data/NC.zip'), name="NC.zip")
    )
    return ds


# load a test stylesheet

# create a test rendered-layer

# test wms capablities

# test wms rendering

# test WMSGetFeatureInfo

# test cache shave

# test cache trim

# test TMS tile rendering

# test layer seeding

# test changing the resource data

# test changing the style

# test changing a single data point

