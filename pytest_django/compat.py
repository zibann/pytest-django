# In Django 1.6, the old test runner was deprecated, and the useful bits were
# moved out of the test runner.

import pytest

try:
    from django.test.runner import DiscoverRunner as DjangoTestRunner
except ImportError:
    from django.test.simple import DjangoTestSuiteRunner as DjangoTestRunner

_runner = DjangoTestRunner(verbosity=pytest.config.option.verbose,
                           interactive=False)


try:
    from django.test.runner import setup_databases
except ImportError:
    setup_databases = _runner.setup_databases

teardown_databases = _runner.teardown_databases

try:
    from django.test.utils import (setup_test_environment,
                                   teardown_test_environment)
except ImportError:
    setup_test_environment = _runner.setup_test_environment
    teardown_test_environment = _runner.teardown_test_environment


del _runner

try:
    from django.test.signals import setting_changed
except ImportError:
    # Django 1.3 does not have the setting_changed signal. Fake that we have it
    # available by defining it ourselves. No listeners will be connected to
    # this instance, so it will not be usable, it just exists here to make
    # compatibilty easier
    from django.dispatch import Signal
    setting_changed = Signal(providing_args=['setting', 'value'])
