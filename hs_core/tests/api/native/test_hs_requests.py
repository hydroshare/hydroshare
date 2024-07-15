from django.test import TestCase
from hs_core.hydroshare import hs_requests
from django.conf import settings


class TestRewrite(TestCase):
    """ Test local rewriting that bypasses firewalls and hits local nginx server """

    def setUp(self):
        self.prod_fqdn = getattr(settings, "PROD_FQDN_OR_IP", "www.hydroshare.org")
        self.fqdn = getattr(settings, "FQDN_OR_IP", "www.hydroshare.org")
        self.hs_ip = hs_requests.get_local_ip()

    def test_localize_outer(self):
        """ rewrite requests to outer host"""
        self.assertEqual(hs_requests.localize_url("https://{}/foo/bar/".format(self.fqdn)),
                         "https://{}/foo/bar/".format(self.hs_ip))
        self.assertEqual(hs_requests.localize_url("http://{}/foo/bar/".format(self.fqdn)),
                         "http://{}/foo/bar/".format(self.hs_ip))

    def test_localize_www(self):
        """ rewrite requests to production host"""
        self.assertEqual(hs_requests.localize_url("https://{}/foo/bar/".format(self.prod_fqdn)),
                         "https://{}/foo/bar/".format(self.hs_ip))
        self.assertEqual(hs_requests.localize_url("http://{}/foo/bar/".format(self.prod_fqdn)),
                         "http://{}/foo/bar/".format(self.hs_ip))

    def test_do_not_localize_others(self):
        """ don't rewrite other host addresses """
        self.assertEqual(hs_requests.localize_url("https://{}/foo/bar/".format("www.foo.com")),
                         "https://{}/foo/bar/".format("www.foo.com"))
        self.assertEqual(hs_requests.localize_url("http://{}/foo/bar/".format("www.foo.com")),
                         "http://{}/foo/bar/".format("www.foo.com"))
