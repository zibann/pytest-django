# In Django 1.6, the old test runner was deprecated, and
# {setup,teardown}_databases was moved out from the test runner class
try:
    from django.test.runner import setup_databases, teardown_databases
except ImportError:
    from django.test.simple import DjangoTestSuiteRunner

    _runner = DjangoTestSuiteRunner(interactive=False)
    setup_databases = _runner.setup_databases
    teardown_databases = _runner.teardown_databases


# OperationalError was introduced in Django 1.6
# Guess OperationalErrors for other databases for older versions of Django
def _get_operational_errors():
    try:
        from django.db.utils import OperationalError
        return OperationalError
    except ImportError:
        errors = []

    try:
        import MySQLdb
        errors.append(MySQLdb.OperationalError)
    except ImportError:
        pass

    try:
        import psycopg2
        errors.append(psycopg2.OperationalError)
    except ImportError:
        pass

    return tuple(errors)

OPERATIONAL_ERRORS = _get_operational_errors()
