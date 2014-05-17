import pytest


class CursorManager(object):
    """Manager for django.db.backends.util.CursorWrapper

    This is the object returned by django_cursor_wrapper.

    If created with None as django.db.backends.util the object is a
    no-op.
    """

    def __init__(self, dbutil=None):
        self.stack = []

        self._dbutil = dbutil
        if dbutil:
            self._orig_wrapper = dbutil.CursorWrapper

    def _blocking_wrapper(*args, **kwargs):
        __tracebackhide__ = True
        __tracebackhide__  # Silence pyflakes
        pytest.fail('Database access not allowed, '
                    'use the "django_db" mark to enable')

    def enable(self):
        """Enable access to the django database"""
        if self._dbutil:
            self.stack.append(self._dbutil.CursorWrapper)
            self._dbutil.CursorWrapper = self._orig_wrapper

    def disable(self):
        if self._dbutil:
            self.stack.append(self._dbutil.CursorWrapper)
            self._dbutil.CursorWrapper = self._blocking_wrapper

    def restore(self):
        assert self.stack, 'no state to pop!'
        self._dbutil.CursorWrapper = self.stack.pop()

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.restore()
