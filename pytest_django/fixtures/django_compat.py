import pytest

from ..lazy_django import django_settings_is_configured
from ..django_compat import is_django_unittest


@pytest.fixture(autouse=True)
def django_setup_unittest(request, django_cursor_wrapper):
    """Setup a django unittest, internal to pytest-django"""
    if django_settings_is_configured() and is_django_unittest(request.node):
        request.getfuncargvalue('django_test_environment')
        request.getfuncargvalue('django_db_setup')
        django_cursor_wrapper.enable()
        request.addfinalizer(django_cursor_wrapper.restore)
