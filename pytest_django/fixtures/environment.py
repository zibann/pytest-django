import pytest

from ..lazy_django import django_settings_is_configured


@pytest.fixture(autouse=True, scope='session')
def django_test_environment(request):
    """
    Sets up the Django test environment, by calling Django's setup_test_environment
    """
    if django_settings_is_configured():
        from django.test.utils import setup_test_environment, teardown_test_environment
        from django.conf import settings
        from ..compat import setup

        setup()  # This is django.setup()

        setup_test_environment()
        settings.DEBUG = False

        request.addfinalizer(teardown_test_environment)


@pytest.fixture(autouse=True, scope='function')
def django_clear_outbox():
    """Clear the django outbox, internal to pytest-django"""
    if django_settings_is_configured():
        from django.core import mail
        mail.outbox = []
