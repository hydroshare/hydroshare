from hs_tools_resource.utils import get_image_type
from django.test import TestCase


class TestToolsResourceUtils(TestCase):

    def test_get_image_type(self):
        try:
            in_file = open("hs_tools_resource/tests/images/wiki_watershed_exif.jpg", "rb")
            image_type = get_image_type(h=in_file.read())
            self.assertEqual("jpeg", image_type)
        except:
            self.fail("Failure occurred while opening or getting image type")
        finally:
            in_file.close()

    def test_bad_get_image_type(self):
        image_type = get_image_type(h=bytearray("garbage", "UTF-8"))
        self.assertEqual(None, image_type)
