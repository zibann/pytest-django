"""All pytest-django fixtures"""

from __future__ import with_statement

import os

import pytest

from . import live_server_helper
from .db_reuse import DjangoTestDatabaseReuse
from .test_db_config import TestDBConfig

from .django_compat import is_django_unittest
from .lazy_django import skip_if_no_django


__all__ = ['django_db_setup', 'django_db', 'django_db_transactional',
           'client', 'admin_client', 'rf', 'settings', 'live_server',
           '_live_server_helper']


@pytest.fixture(scope='session')
def django_test_db_config(request, django_test_environment):
    """Make sure the databases are configured to point to test mirrors"""

    skip_if_no_django()

    # Add xdist "gw0", "gw1", ... suffixes to the test database name
    if hasattr(request.config, 'slaveinput'):
        suffix = request.config.slaveinput['slaveid']
    else:
        suffix = None

    test_db_config = TestDBConfig(suffix)
    test_db_config.set_test_names()

    return test_db_config


@pytest.fixture(scope='session')
def django_db_reuse(request, django_cursor_wrapper):
    """An instance of DjangoTestDatabaseReuse."""
    return DjangoTestDatabaseReuse(request.config, django_cursor_wrapper)


@pytest.fixture(scope='session')
def django_db_setup(request,
                    django_test_db_config,
                    django_test_environment,
                    django_cursor_wrapper,
                    django_db_reuse):
    """Session-wide database setup, internal to pytest-django"""
    skip_if_no_django()

    from .compat import setup_databases, teardown_databases
    from django.conf import settings

    # Run souths syncdb command if south is installed. The call to
    # patch_for_test_db_setup ensures that migrations are run
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    # Replace Django's database test creation creation code to support database reuse
    if django_db_reuse.can_reuse_database():
        django_db_reuse.monkeypatch_django_creation()

    with django_cursor_wrapper:
        db_cfg = setup_databases()

    if django_db_reuse.should_drop_database():
        def fin():
            with django_cursor_wrapper:
                teardown_databases(db_cfg)

        request.addfinalizer(fin)


@pytest.fixture(scope='function')
def django_db(request, django_db_setup, django_cursor_wrapper):
    """Require a django test database

    This database will be setup with the default fixtures and will
    have the transaction management disabled.  At the end of the test
    the transaction will be rolled back to undo any changes to the
    database.  This is more limited then the ``transaction_db``
    resource but faster.

    If both this and ``transaction_db`` are requested then the
    database setup will behave as only ``transaction_db`` was
    requested.
    """

    is_django_testcase = ('django_db_transactional' not in request.funcargnames and
                          'live_server' not in request.funcargnames and
                          not is_django_unittest(request.node))

    if is_django_testcase:

        from django.test import TestCase

        django_cursor_wrapper.enable()

        case = TestCase(methodName='__init__')
        case._pre_setup()
        request.addfinalizer(django_cursor_wrapper.restore)
        request.addfinalizer(case._post_teardown)


@pytest.fixture(scope='function')
def django_db_transactional(request, django_db_setup, django_cursor_wrapper):
    """Require a django test database with transaction support

    This will re-initialise the django database for each test and is
    thus slower then the normal ``db`` fixture.

    If you want to use the database with transactions you must request
    this resource.  If both this and ``db`` are requested then the
    database setup will behave as only ``transaction_db`` was
    requested.
    """
    if not is_django_unittest(request.node):
        django_cursor_wrapper.enable()

        def flushdb():
            """Flush the database and close database connections"""
            # Django does this by default *before* each test
            # instead of after.
            from django.db import connections
            from django.core.management import call_command

            for db in connections:
                call_command('flush', verbosity=0, interactive=False, database=db)
            for conn in connections.all():
                conn.close()

        request.addfinalizer(django_cursor_wrapper.restore)
        request.addfinalizer(flushdb)


@pytest.fixture()
def client():
    """A Django test client instance"""
    skip_if_no_django()
    from django.test.client import Client
    return Client()


@pytest.fixture()
def admin_client(client, django_db):
    skip_if_no_django()

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
    except ImportError:
        from django.contrib.auth.models import User

    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@example.com', 'password')
        user.is_staff = True
        user.is_superuser = True
        user.save()

    client.login(username='admin', password='password')

    return client


@pytest.fixture()
def rf():
    """RequestFactory instance"""
    skip_if_no_django()

    from django.test.client import RequestFactory

    return RequestFactory()


class MonkeyPatchWrapper(object):
    def __init__(self, monkeypatch, wrapped_object):
        super(MonkeyPatchWrapper, self).__setattr__('monkeypatch', monkeypatch)
        super(MonkeyPatchWrapper, self).__setattr__('wrapped_object',
                                                    wrapped_object)

    def __getattr__(self, attr):
        return getattr(self.wrapped_object, attr)

    def __setattr__(self, attr, value):
        self.monkeypatch.setattr(self.wrapped_object, attr, value,
                                 raising=False)

    def __delattr__(self, attr):
        self.monkeypatch.delattr(self.wrapped_object, attr)


@pytest.fixture()
def settings(request, monkeypatch):
    """A Django settings object which restores changes after the testrun"""
    skip_if_no_django()

    from django.conf import settings as django_settings
    return MonkeyPatchWrapper(monkeypatch, django_settings)


@pytest.fixture(scope='session')
def live_server(request):
    """Run a live Django server in the background during tests

    The address the server is started from is taken from the
    --liveserver command line option or if this is not provided from
    the DJANGO_LIVE_TEST_SERVER_ADDRESS environment variable.  If
    neither is provided ``localhost:8081,8100-8200`` is used.  See the
    Django documentation for it's full syntax.

    NOTE: If the live server needs database access to handle a request
          your test will have to request database access.  Furthermore
          when the tests want to see data added by the live-server (or
          the other way around) transactional database access will be
          needed as data inside a transaction is not shared between
          the live server and test code.
    """
    skip_if_no_django()
    addr = request.config.getvalue('liveserver')
    if not addr:
        addr = os.getenv('DJANGO_TEST_LIVE_SERVER_ADDRESS')
    if not addr:
        addr = 'localhost:8081,8100-8200'
    server = live_server_helper.LiveServer(addr)
    request.addfinalizer(server.stop)
    return server


@pytest.fixture(autouse=True, scope='function')
def _live_server_helper(request):
    """Helper to make live_server work, internal to pytest-django

    This helper will dynamically request the django_db_transactional fixture
    for a tests which uses the live_server fixture.  This allows the
    server and test to access the database without having to mark
    this explicitly which is handy since it is usually required and
    matches the Django behaviour.

    The separate helper is required since live_server can not request
    django_db_transactional directly since it is session scoped instead of
    function-scoped.
    """
    if 'live_server' in request.funcargnames:
        request.getfuncargvalue('django_db_transactional')
