import os
import sys

import pytest

from .fixtures.database import *
from .fixtures.django_compat import *
from .fixtures.environment import *
from .fixtures.helpers import *
from .fixtures.live_server import *


SETTINGS_MODULE_ENV = 'DJANGO_SETTINGS_MODULE'
CONFIGURATION_ENV = 'DJANGO_CONFIGURATION'


def pytest_addoption(parser):
    group = parser.getgroup('django')
    group._addoption('--reuse-db',
                     action='store_true', dest='reuse_db', default=False,
                     help='Re-use the testing database if it already exists, '
                          'and do not remove it when the test finishes. This '
                          'option will be ignored when --no-db is given.')
    group._addoption('--create-db',
                     action='store_true', dest='create_db', default=False,
                     help='Re-create the database, even if it exists. This '
                          'option will be ignored if not --reuse-db is given.')
    group._addoption('--ds',
                     action='store', type='string', dest='ds', default=None,
                     help='Set DJANGO_SETTINGS_MODULE.')
    group._addoption('--dc',
                     action='store', type='string', dest='dc', default=None,
                     help='Set DJANGO_CONFIGURATION.')
    parser.addini(CONFIGURATION_ENV,
                  'django-configurations class to use by pytest-django.')
    group._addoption('--liveserver', default=None,
                     help='Address and port for the live_server fixture.')
    parser.addini(SETTINGS_MODULE_ENV,
                  'Django settings module to use by pytest-django.')


def _load_settings(config, options):
    # Configure DJANGO_SETTINGS_MODULE
    ds = (options.ds or
          config.getini(SETTINGS_MODULE_ENV) or
          os.environ.get(SETTINGS_MODULE_ENV))

    # Configure DJANGO_CONFIGURATION
    dc = (options.dc or
          config.getini(CONFIGURATION_ENV) or
          os.environ.get(CONFIGURATION_ENV))

    if ds:
        os.environ[SETTINGS_MODULE_ENV] = ds

        if dc:
            os.environ[CONFIGURATION_ENV] = dc

            # Install the django-configurations importer
            import configurations.importer
            configurations.importer.install()

        from django.conf import settings
        try:
            settings.DATABASES
        except ImportError:
            e = sys.exc_info()[1]
            raise pytest.UsageError(*e.args)


if pytest.__version__[:3] >= "2.4":
    def pytest_load_initial_conftests(early_config, parser, args):
        _load_settings(early_config, parser.parse_known_args(args))


def pytest_configure(config):
    # Register the marks
    config.addinivalue_line(
        'markers',
        'django_db(transaction=False): Mark the test as using '
        'the django test database.  The *transaction* argument marks will '
        "allow you to use real transactions in the test like Django's "
        'TransactionTestCase.')
    config.addinivalue_line(
        'markers',
        'urls(modstr): Use a different URLconf for this test, similar to '
        'the `urls` attribute of Django `TestCase` objects.  *modstr* is '
        'a string specifying the module of a URL config, e.g. '
        '"my_app.test_urls".')

    if pytest.__version__[:3] < "2.4":
        _load_settings(config, config.option)
