from uuid import uuid4
import shutil

from django.core.files import File
from pandas import merge, Series
from ga_resources import models
import sh
import os


class Driver(object):
    def __init__(self, resource):
        self.resource = resource

    def get_dataset(self, *args, **kwargs):
        """
        Return a raw dataset, possibly responding to query parameters, but this is not essential.  The dataset must
        contain at least the join key mentioned in the definition of the RelatedResource.  This dataset will be used by
        the driver to join to the parent dataset.  The raw dataset should be a Pandas Panel or DataFrame object.
        """
        raise NotImplementedError

    def as_dataframe(self, *args, **kwargs):
        """Take the data from .dataset() and perform the join on the original data"""
        original_df = self.resource.foreign_resource.driver_instance.as_dataframe(**kwargs['foreign'] if 'foreign' in kwargs else {})
        my_df = self.get_dataset(*args, **kwargs)

        if self.resource.key_transform == models.RelatedResource.CAPITALIZE:
            my_df[self.resource.local_key] = Series(key.capitalize() for key in my_df[self.resource.local_key])
        elif self.resource.key_transform == models.RelatedResource.UPPER:
            my_df[self.resource.local_key] = Series(key.upper() for key in my_df[self.resource.local_key])
        elif self.resource.key_transform == models.RelatedResource.LOWER:
            my_df[self.resource.local_key] = Series(key.lower() for key in my_df[self.resource.local_key])

        resulting_dataframe = merge(
            original_df,
            my_df,
            how=self.resource.how,
            left_on = self.resource.foreign_key,
            right_on = self.resource.local_key,
            left_index = self.resource.left_index,
            right_index = self.resource.right_index,
            sort = False
        )
        return resulting_dataframe # as soon as this is working, cache the ever living crap out of it


    def save_as_new_datasource(self, dataset_title, parent=None, *args, **kwargs):
        df = self.as_dataframe(*args, **kwargs)
        tempfile = uuid4()
        tempfile = os.path.join('/tmp', tempfile.hex)
        self.resource.foreign_resource.driver_instance.from_dataframe(df, tempfile, self.resource.foreign_resource.srs)
        sh.zip('-r', tempfile + '.zip', sh.glob(tempfile + "/*"))

        with open(tempfile + '.zip') as input:
            ds = models.DataResource.objects.create(
                title = dataset_title,
                parent = parent if parent else self.resource.parent,
                resource_file = File(input)
            )

        os.unlink(tempfile + '.zip')
        shutil.rmtree(tempfile)

        return ds



