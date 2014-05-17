"""All pytest-django fixtures"""

from __future__ import with_statement


import pytest

from ..db_reuse import DjangoTestDatabaseReuse
from ..test_db_config import TestDBConfig

from ..django_compat import is_django_unittest
from ..lazy_django import skip_if_no_django, django_settings_is_configured
from ..cursor_manager import CursorManager


@pytest.fixture(scope='session')
def django_test_db_config(request, django_test_environment):
    """Make sure the databases are configured to point to test mirrors"""

    skip_if_no_django()

    # Add xdist "gw0", "gw1", ... suffixes to the test database name
    if hasattr(request.config, 'slaveinput'):
        suffix = request.config.slaveinput['slaveid']
    else:
        suffix = None

    from django.db import connections
    test_db_config = TestDBConfig(connections, suffix)
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
    skip_if_no_django()

    from ..compat import setup_databases, teardown_databases

    from django.conf import settings

    # Run souths syncdb command if south is installed. The call to
    # patch_for_test_db_setup ensures that migrations are run
    if 'south' in settings.INSTALLED_APPS:
        from south.management.commands import patch_for_test_db_setup
        patch_for_test_db_setup()

    # Patch Django's database test creation creation code to support database reuse
    if django_db_reuse.can_reuse_database():
        django_db_reuse.monkeypatch_django_creation()

    with django_cursor_wrapper:
        db_cfg = setup_databases(1, interactive=False)

    if django_db_reuse.should_drop_database():
        def finalizer():
            with django_cursor_wrapper:
                teardown_databases(db_cfg)

        request.addfinalizer(finalizer)


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

    wrap_in_transaction = ('django_db_transactional' not in request.funcargnames and
                           'live_server' not in request.funcargnames and
                           not is_django_unittest(request.node))

    django_cursor_wrapper.enable()

    if wrap_in_transaction:
        from django.test import TestCase
        case = TestCase(methodName='__init__')
        case._pre_setup()

    request.addfinalizer(django_cursor_wrapper.restore)

    if wrap_in_transaction:
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


@pytest.fixture(autouse=True, scope='session')
def django_cursor_wrapper(request):
    """The django cursor wrapper, internal to pytest-django

    This will globally disable all database access. The object returned has a
    .enable() and a .disable() method which can be used to temporarily enable
    database access. The previous state of database access mode can then be
    restore by calling .restore()

    It can also be used as a context manager.
    """
    if django_settings_is_configured():

        # util -> utils rename in Django 1.7
        try:
            import django.db.backends.utils
            utils_module = django.db.backends.utils
        except ImportError:
            import django.db.backends.util
            utils_module = django.db.backends.util

        manager = CursorManager(utils_module)
        manager.disable()
        request.addfinalizer(manager.restore)
    else:
        manager = CursorManager()
    return manager


def _validate_django_db(marker):
    """This function validates the django_db marker

    It checks the signature and creates the `transaction` attribute on
    the marker which will have the correct value.
    """
    def apifun(transaction=False):
        marker.transaction = transaction
    apifun(*marker.args, **marker.kwargs)


@pytest.fixture(autouse=True)
def django_db_marker(request):
    """Implement the django_db marker, internal to pytest-django

    This will dynamically request the ``db`` or ``django_db_transactional``
    fixtures as required by the django_db marker.
    """
    marker = request.node.get_marker('django_db')

    if marker:
        _validate_django_db(marker)
        if marker.transaction:
            request.getfuncargvalue('django_db_transactional')
        else:
            request.getfuncargvalue('django_db')
