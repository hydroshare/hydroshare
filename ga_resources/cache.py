from django.conf import settings

class ResourceCache(object):
    def __init__(self):
        self.redis = settings.WMS_CACHE_DB

    def store_data(self, filename, data):
        pass

    def store_file(self, filename, stream):
        pass

    def store_url(self, filename, url):
        pass

    def open(self, filename):
        pass

    def rm(self, *filenames):
        pass



