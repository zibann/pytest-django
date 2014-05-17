import sys
import types


def monkeypatch_method(obj, method_name, new_method):
    assert hasattr(obj, method_name)

    if sys.version_info < (3, 0):
        wrapped_method = types.MethodType(new_method, obj, obj.__class__)
    else:
        wrapped_method = types.MethodType(new_method, obj)

    setattr(obj, method_name, wrapped_method)


def is_in_memory_db(connection):
    """Return whether it makes any sense to use REUSE_DB with the backend of a
    connection."""
    # This is a SQLite in-memory DB. Those are created implicitly when
    # you try to connect to them, so our test below doesn't work.
    return connection.settings_dict['NAME'] == ':memory:'
