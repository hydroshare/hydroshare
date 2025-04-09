
from django.test.runner import DiscoverRunner
from django.conf import settings
from xmlrunner.extra.djangotestrunner import XMLTestRunner

from celery import current_app


def _set_eager():
    """
    Allow tests to successfully interact with Celery, as per:

    http://docs.celeryproject.org/en/2.5/django/unit-testing.html

    Adapted from:

    https://github.com/celery/django-celery/blob/master/djcelery/contrib/test_runner.py
    :return:
    """
    settings.CELERY_ALWAYS_EAGER = True
    current_app.conf.CELERY_ALWAYS_EAGER = True
    settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Issue #75
    current_app.conf.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True


class CustomTestSuiteRunner(DiscoverRunner):
    """Override the default django 'test' command, exclude from testing
    all 3rd part apps which we know will probably fail."""

    def setup_test_environment(self, **kwargs):
        """
        Adapted from:

        https://github.com/celery/django-celery/blob/master/djcelery/contrib/test_runner.py
        :param kwargs:
        :return:
        """
        _set_eager()
        super(CustomTestSuiteRunner, self).setup_test_environment(**kwargs)

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels:
            # No appnames specified on the command line, so we run all
            # tests, but remove those which we know are troublesome.

            test_labels = [app for app in settings.INSTALLED_APPS if app not in settings.APPS_TO_NOT_RUN
                           and (not app.startswith('django.') and not app.startswith('mezzanine.'))]

        return super(CustomTestSuiteRunner, self).run_tests(test_labels, extra_tests, **kwargs)


class CustomXmlRunner(CustomTestSuiteRunner, XMLTestRunner):
    """
    Custom test runner that uses XMLTestRunner to output results in XML format.
    This is useful for CI/CD pipelines and other automated testing environments.
    """
    pass
