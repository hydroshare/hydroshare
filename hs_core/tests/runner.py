__author__ = 'Pabitra'

from django_nose.runner import NoseTestSuiteRunner
from hydroshare import settings

class CustomTestSuiteRunner(NoseTestSuiteRunner):
    """Override the default django 'test' command, exclude from testing
    all 3rd part apps which we know will probably fail."""

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels:
            # No appnames specified on the command line, so we run all
            # tests, but remove those which we know are troublesome.

            test_labels = [app for app in settings.INSTALLED_APPS if app not in settings.APPS_TO_NOT_RUN
                           and (not app.startswith('django.') and not app.startswith('mezzanine.'))]

        return super(CustomTestSuiteRunner, self).run_tests(test_labels, extra_tests, **kwargs)
