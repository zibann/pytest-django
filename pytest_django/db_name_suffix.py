from .utils import monkeypatch_method


def monkey_patch_creation_for_db_suffix(suffix):
    assert suffix

    def _get_test_db_name(self):
        """
        Internal implementation - returns the name of the test DB that will be
        created. Only useful when called from create_test_db() and
        _create_test_db() and when no external munging is done with the 'NAME'
        or 'TEST_NAME' settings.
        """

        if self.connection.settings_dict['TEST_NAME']:
            original = self.connection.settings_dict['TEST_NAME']

        original = 'test_' + self.connection.settings_dict['NAME']

        return '%s_%s' % (original, suffix)

    from django.db import connections

    for connection in connections.all():
        monkeypatch_method(connection.creation, '_get_test_db_name', _get_test_db_name)
