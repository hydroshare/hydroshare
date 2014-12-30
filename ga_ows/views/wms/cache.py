from bson import Binary
import hashlib
import pymongo

class WMSCache(object):
    """The WMS Cache, based on MongoDB.

    Public Members:

    * self.collection : the PyMongo collection object.  See the PyMongo API for how to use this.
    """
    def __init__(self, route='default', collection='wms_cache', *locators):
        """
        :param route: The MongoDB route as listed in settings.MONGODB_ROUTES
        :param collection: The Mongo collection to use for this cache
        :param locators: Locator keys that need to be indexed to find items by something other than primary key.
        :return:
        """

        #: ..

        if not hasattr(settings, 'MONGODB_ROUTES'):
            raise EnvironmentError('Settings must contain MONGODB_ROUTES')

        if route in settings.MONGODB_ROUTES:
            self.collection = settings.MONGODB_ROUTES[route][collection]
        else:
            self.collection = settings.MONGODB_ROUTES['default'][collection]

        self.collection.ensure_index([("_creation_time", pymongo.DESCENDING)])
        self.collection.ensure_index([("_used_time", pymongo.DESCENDING)])

    def save(self, item, **keys):
        """ Save or update a cache item.
        :param item: The item to save.
        :param keys: The keys to save the item under.  Must be serializable by PyMongo.
        :return:
        """
        document = keys
        docid = hashlib.new('md5')
        docid.update(str(sorted(keys.items())))
        docid = docid.hexdigest()

        document['_id'] = docid
        document['_item'] = Binary(item)
        document['_creation_time'] = datetime.utcnow()
        document['_used_time'] = document['_creation_time']
        self.collection.save(document)

    def locate(self, **keys):
        """ Find a single item in the cache.
        :param keys:
        :return:
        """
        docid = hashlib.new("md5")
        docid.update(str(sorted(keys.items())))
        docid = docid.hexdigest()

        item = self.collection.find_and_modify({ '_id' : docid }, {"$set" : {'_used_time' : datetime.utcnow() }})
        if item:
            return item['_item']
        else:
            return None

    def collect(self, **keys):
        """ Find all the items that match particular keys in the cache.
        :param keys: A list of keys.
        :return:
        """
        return self.collection.find(keys)

    def flush(self):
        """
        Delete the cache entirely.
        """
        self.collection.drop()

    def flush_older(self, when, **kwargs):
        """
        Delete cache entries older than a given time that also match a set of criteria.

        :param when: A datetime object in the same time zone as the objects in the cache (prefer UTC)
        :param kwargs: A set of pymongo query descriptors.  See `http://mongodb.org`_ for more details.
        """
        kwargs['_creation_time'] = {'$lte', when }
        self.collection.remove(kwargs)

    def flush_lru(self, count):
        """
        Flush the least-recently-used keys in the cache until there are no more than [count] objects in the cache

        :param count: The cap of the number of remaining objects in the cache.
        """
        total = self.collection.count()
        if total > count:
            key = self.collection.find().sort(('_used_time', pymongo.DESCENDING))[count]
            key = key['_used_time']
            self.collection.remove({ '_used_time' : {'$lte' : key}})

    @staticmethod
    def for_geodjango_model(model, route='default'):
        """Return a specialized instance for a GeoDjango model.
        :param model: The model class itself
        :param route: The MongoDB route to use.
        :return: A WMSCache object specialized to a GeoDjango model
        """
        return WMSCache(route, model._meta.app_label + "_" + model._meta.module_name + "__wms_cache", "model")

    class GeoDjangoCacheInvalidatingignalHandler(object):
        """ When connected to Django's post_save signal, this invalidates the WMS cache for a model when an instance of a
            model class is saved, created, or updated. Usage is similar to::

                from django.signals import post_save, post_delete, m2m_changed

                handler = WMSCache.GeoDjangoCacheInvalidatingSignalHandler(models.CensusCounty)
                post_save.connect(handler)
                post_delete.connect(handler)
                m2m_changed.connect(handler)

            This is a fairly blunt instrument.  A better signal handler would actually look for the bounding boxes of the
            cached tiles and find all the tiles that actually change due to the modification of the database.  However,
            this will work.
        """
        def __init__(self, model, cache=None):
            """
            :param model: The sender model to invalidate
            :param cache: The cache instance that contains the instances
            :return:
            """
            self.looking_for = model
            if cache:
                self.cache = cache
            else:
                self.cache = WMSCache.for_geodjango_model(model)

        def __call__(self, sender, **kwargs):
            if sender == self.looking_for:
                self.cache.collect(model=sender._meta.object_name).remove()
