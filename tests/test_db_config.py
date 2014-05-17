# -*- coding: utf-8 -*-

from django.db.utils import ConnectionHandler

from pytest_django.test_db_config import TestDBConfig


def test_name_without_suffix():
    connections = ConnectionHandler({
        'default': {
            'ENGINE': 'django.db.backends.dummy',
            'NAME': 'foo',
            'TEST_NAME': '',
        }
    })

    test_db_config = TestDBConfig(connections, suffix=None)
    test_db_config.set_test_names()

    assert connections['default'].settings_dict['TEST_NAME'] == 'test_foo'


def test_name_with_suffix():
    connections = ConnectionHandler({
        'default': {
            'ENGINE': 'django.db.backends.dummy',
            'NAME': 'foo',
            'TEST_NAME': '',
        }
    })

    test_db_config = TestDBConfig(connections, suffix='abc')
    test_db_config.set_test_names()

    assert connections['default'].settings_dict['TEST_NAME'] == 'test_foo_abc'


def test_do_not_override_test_name_when_exists():
    connections = ConnectionHandler({
        'default': {
            'ENGINE': 'django.db.backends.dummy',
            'NAME': 'foo',
            'TEST_NAME': 'use_this',
        }
    })

    test_db_config = TestDBConfig(connections, suffix=None)
    test_db_config.set_test_names()

    assert connections['default'].settings_dict['TEST_NAME'] == 'use_this'

def test_do_not_override_test_name_when_exists_with_suffix():
    connections = ConnectionHandler({
        'default': {
            'ENGINE': 'django.db.backends.dummy',
            'NAME': 'foo',
            'TEST_NAME': 'foobar',
        }
    })

    test_db_config = TestDBConfig(connections, suffix='abc')
    test_db_config.set_test_names()

    assert connections['default'].settings_dict['TEST_NAME'] == 'foobar_abc'
