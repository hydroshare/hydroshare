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
            APPS_TO_NOT_RUN = (
                'ga_ows',
                'ga_resources',
                'jquery_ui',
                'djcelery',
                'rest_framework',
                'django_docker_processes',
                'dublincore',
                'django_nose',
                'inplaceeditform',
                'grappelli_safe',
                'django_irods',
                'crispy_forms',
                'autocomplete_light',
                'widget_tweaks',
                'hs_tools_resource',  #TODO: remove this app from this testing black list after resource class refactoring
                'ref_ts'    #TODO: remove this app from this testing black list after resource class refactoring
                # etc...
            )

            test_labels = [app for app in settings.INSTALLED_APPS if app not in APPS_TO_NOT_RUN
                           and (not app.startswith('django.') and not app.startswith('mezzanine.'))]

        return super(CustomTestSuiteRunner, self).run_tests(test_labels, extra_tests, **kwargs)