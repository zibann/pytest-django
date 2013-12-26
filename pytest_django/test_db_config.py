class TestDBConfig(object):
    """
    Helper class to modify TEST_NAME and NAME to point to test databases.
    """

    def __init__(self, suffix):
        self.suffix = suffix
        self._test_names_set = False

    def set_test_names(self):
        """
        Set TEST_NAME for each database connection. This method should be
        called before calling setup_databases() to be compatible with xdist.
        """
        if self._test_names_set:
            return

        self._test_names_set = True

        from django.db import connections

        for connection in connections.all():
            test_name = connection.settings_dict.get('TEST_NAME')

            if test_name is None:
                test_name = 'test_%s' % connection.settings_dict['NAME']

            if self.suffix:
                test_name += '_%s' % self.suffix

            connection.settings_dict['TEST_NAME'] = test_name

    def set_names(self):
        """
        Set NAME for each database connection to the test database name. This
        method should be called before manually creating test databases.
        """
        self.set_test_names()
        from django.db import connections

        for connection in connections.all():
            connection.close()  # Close any existing connections
            connection.settings_dict['NAME'] = connection.settings_dict['TEST_NAME']
