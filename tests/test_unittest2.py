
def test_unittest2_no_db(django_testdir):

    django_testdir.create_test_module('''
import unittest2

from .app.models import Item

class TestSomething(unittest2.TestCase):
    def test_foo(self):
        assert Item.objects.count() == 0
''')

    result = django_testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        '*Failed: Database access not allowed, use the "django_db" mark to enable*'
    ])
    assert result.ret == 1


def test_unittest2_with_db(django_testdir):

    django_testdir.create_test_module('''
import pytest

import unittest2

from .app.models import Item

pytestmark = pytest.mark.django_db

class TestSomething(unittest2.TestCase):
    def test_foo(self):
        assert Item.objects.count() == 0
''')

    result = django_testdir.runpytest('-v')
    result.stdout.fnmatch_lines([
        '*TestSomething.test_foo PASSED*'
    ])
    assert result.ret == 0
