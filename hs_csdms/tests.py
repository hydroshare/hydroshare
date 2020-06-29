from django.test import TransactionTestCase
from hs_core.testing import TestCaseCommonUtilities
from hs_access_control.tests.utilities import global_reset
from hs_csdms.models import CSDMSName


class TestCSDMSName(TestCaseCommonUtilities, TransactionTestCase):
    def setUp(self):
        super(TestCSDMSName, self).setUp()
        global_reset()

    def test_csdms_name(self):
        csdms_name = CSDMSName.add_word('CSDMSName', 'name', 'cat')
        csdms_decoration = CSDMSName.add_word('CSDMSName', 'decoration', 'cute')
        csdms_measure = CSDMSName.add_word('CSDMSName', 'measure', 'ft')
        self.assertEqual(csdms_name.value, 'cat')
        self.assertEqual(csdms_decoration.value, 'cute')
        self.assertEqual(csdms_measure.value, 'ft')
