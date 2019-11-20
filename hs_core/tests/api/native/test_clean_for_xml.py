from django.test import TestCase
from hs_core.models import clean_for_xml


class TestCleaning(TestCase):

    def test_convert_newlines(self):
        """ convert single newlines to SYMBOL return """
        self.assertEqual(clean_for_xml(u"it\nis\nfinished"),
                         u"it \u23ce is \u23ce finished")

    def test_convert_newlines_2(self):
        """ convert double newlines to SYMBOL paragraph """
        self.assertEqual(clean_for_xml(u"it\n\nis\n\nfinished"),
                         u"it \u00b6 is \u00b6 finished")

    def test_convert_newlines_3(self):
        """ embedded spaces do not change SYMBOL paragraph conversion """
        self.assertEqual(clean_for_xml(u"it \n \n is \n \n finished"),
                         u"it \u00b6 is \u00b6 finished")

    def test_convert_newlines_4(self):
        """ embedded returns do not change SYMBOL return conversion """
        self.assertEqual(clean_for_xml(u"it \r\n is \r\n finished"),
                         u"it \u23ce is \u23ce finished")

    def test_convert_newlines_5(self):
        """ embedded returns do not change SYMBOL paragraph conversion """
        self.assertEqual(clean_for_xml(u"it \r\n \r\n is \r\n \r\n finished"),
                         u"it \u00b6 is \u00b6 finished")

    def test_convert_newlines_6(self):
        """ embedded control characters do not change SYMBOL paragraph conversion """
        self.assertEqual(clean_for_xml(u"it \n\u0003\n is \n\u0003\n finished"),
                         u"it \u00b6 is \u00b6 finished")

    def test_convert_newlines_7(self):
        """ embedded control characters in words are converted to spaces """
        self.assertEqual(clean_for_xml(u"it \n \n i\u0003s \n \n finished"),
                         u"it \u00b6 i s \u00b6 finished")

    def test_convert_newlines_8(self):
        """ complete nonsense is converted to one space """
        self.assertEqual(clean_for_xml(u"it \n\u0003\u0004 \n i\u0003\u0006\u0001s \n \n finished"),
                         u"it \u00b6 i s \u00b6 finished")

    def test_convert_newlines_9(self):
        """ arbitrary numbers of newlines become one paragraph """
        self.assertEqual(clean_for_xml(u"it \n\n\r\n\r\n is \n\n\n\n finished"),
                         u"it \u00b6 is \u00b6 finished")
