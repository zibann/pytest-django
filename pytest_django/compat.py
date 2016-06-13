# In Django 1.6, the old test runner was deprecated, and the useful bits were
# moved out of the test runner.

import pytest

from django.conf import settings
from django.test.utils import get_runner

try:
    from django.test.runner import DiscoverRunner as DjangoTestRunner
except ImportError:
    from django.test.simple import DjangoTestSuiteRunner as DjangoTestRunner

DjangoTestRunner = get_runner(settings)
_runner = DjangoTestRunner(verbosity=pytest.config.option.verbose,
                           interactive=False)


setup_databases = _runner.setup_databases

teardown_databases = _runner.teardown_databases

try:
    from django.test.utils import (setup_test_environment,
                                   teardown_test_environment)
except ImportError:
    setup_test_environment = _runner.setup_test_environment
    teardown_test_environment = _runner.teardown_test_environment


del _runner
