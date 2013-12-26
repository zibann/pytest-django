"""Functions to aid in preserving the test database between test runs.

The code in this module is heavily inspired by django-nose:
https://github.com/jbalogh/django-nose/
"""
from .utils import monkeypatch_method


class DjangoTestDatabaseReuse(object):
    def __init__(self, config):
        self.config = config

    def can_reuse_database(self):
        return self.config.getvalue('reuse_db') and not self.config.getvalue('create_db')

    def should_drop_database(self):
        return not self.config.getvalue('reuse_db')

    def monkeypatch_django_creation(self, django_cursor_wrapper):
        from django.db import connections

        def create_test_db_with_reuse(self, verbosity=1, autoclobber=False):
            """
            This method is a monkey patched version of create_test_db that
            will not actually create a new database, but just reuse the
            existing.
            """
            test_database_name = self._get_test_db_name()
            self.connection.settings_dict['NAME'] = test_database_name

            if verbosity >= 1:
                test_db_repr = ''
                if verbosity >= 2:
                    test_db_repr = " ('%s')" % test_database_name
                print("Re-using existing test database for alias '%s'%s..." % (
                    self.connection.alias, test_db_repr))

            # confirm() is not needed/available in Django >= 1.5
            # See https://code.djangoproject.com/ticket/17760
            if hasattr(self.connection.features, 'confirm'):
                self.connection.features.confirm()

            return test_database_name

        with django_cursor_wrapper:
            for connection in connections.all():
                if _test_database_exists_from_previous_run(connection):
                    monkeypatch_method(connection.creation, 'create_test_db', create_test_db_with_reuse)


def _is_in_memory_db(connection):
    """Return whether it makes any sense to use REUSE_DB with the backend of a
    connection."""
    # This is a SQLite in-memory DB. Those are created implicitly when
    # you try to connect to them, so our test below doesn't work.
    return connection.settings_dict['NAME'] == ':memory:'


def _test_database_exists_from_previous_run(connection):
    from django.db.utils import OperationalError

    # Check for sqlite memory databases
    if _is_in_memory_db(connection):
        return False

    connection.close()

    # Try to open a cursor to the test database
    orig_db_name = connection.settings_dict['NAME']
    connection.settings_dict['NAME'] = connection.creation._get_test_db_name()

    try:
        connection.cursor()
        return True
    except OperationalError:
        return False
    finally:
        connection.close()
        connection.settings_dict['NAME'] = orig_db_name
