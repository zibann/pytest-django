from .utils import is_in_memory_db


class TestDBConfig(object):
    """
    Helper class to modify TEST_NAME and NAME to point to test databases.
    """

    def __init__(self, connections, suffix):
        self._suffix = suffix
        self._connections = connections
        self._test_names_set = False

    def set_test_names(self):
        """
        Set TEST_NAME for each database connection. This method should be
        called before calling setup_databases() to be compatible with xdist.
        """
        assert not self._test_names_set
        self._test_names_set = True

        for connection in self._connections.all():
            # Do not bother setting TEST_NAME for in memory databases
            if is_in_memory_db(connection):
                continue

            test_name = connection.settings_dict.get('TEST_NAME')

            if not test_name:
                test_name = 'test_%s' % connection.settings_dict['NAME']

            if self._suffix:
                test_name += '_%s' % self._suffix

            connection.settings_dict['TEST_NAME'] = test_name
