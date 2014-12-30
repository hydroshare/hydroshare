from unittest import TestCase, skip
from . import utils

@skip
class TestWMS(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = utils.load_example_dataset_from_filesystem()

    def test_GetCapabilities(self):
        self.fail('not written yet')

    def test_GetFeature(self):
        self.fail('not written yet')

    def test_TMSGetTile(self):
        self.fail('not written yet')

    #def test_GetFeatureInfo(self):
    #    self.fail('not written yet')

