# In Django 1.6, the old test runner was deprecated, and
# {setup,teardown}_databases was moved out from the test runner class
try:
    from django.test.runner import setup_databases, teardown_databases
except ImportError:
    from django.test.simple import DjangoTestSuiteRunner

    _runner = DjangoTestSuiteRunner()
    setup_databases = _runner.setup_databases
    teardown_databases = _runner.teardown_databases
