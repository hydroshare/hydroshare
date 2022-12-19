# run with: python manage.py test hs_core.tests.serialization.test_generic_resource_meta
import unittest

from hs_core.serialization import GenericResourceMeta


class TestGenericResourceMeta(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_creator_ordering(self):

        rmeta = GenericResourceMeta()

        creator1 = GenericResourceMeta.ResourceCreator()
        creator1.order = 7
        creator1.name = "John Smith"
        creator1.uri = "http://akebono.stanford.edu/yahoo/"
        rmeta.add_creator(creator1)

        creator2 = GenericResourceMeta.ResourceCreator()
        creator2.order = 8
        creator2.name = "Johnny Appleseed"
        creator2.uri = "http://www.foo.com/"
        rmeta.add_creator(creator2)

        creator3 = GenericResourceMeta.ResourceCreator()
        creator3.order = 1
        creator3.name = "Pharoah Sanders"
        creator3.uri = "gopher://gopher.mit.edu"
        rmeta.add_creator(creator3)

        creators = rmeta.get_creators()
        self.assertEqual(len(creators), 3)
        self.assertEqual(creators[0].name, creator3.name)
        self.assertEqual(creators[1].name, creator1.name)
        self.assertEqual(creators[2].name, creator2.name)

        owner_uri = rmeta.get_owner().uri
        self.assertEqual(owner_uri, creator3.uri)
