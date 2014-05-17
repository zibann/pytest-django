import os
import pytest

from ..lazy_django import skip_if_no_django
from ..live_server import LiveServer


@pytest.fixture(scope='session')
def live_server_session(request):
    """Run a live Django server in the background during tests

    The address the server is started from is taken from the
    --liveserver command line option or if this is not provided from
    the DJANGO_LIVE_TEST_SERVER_ADDRESS environment variable.  If
    neither is provided ``localhost:8081,8100-8200`` is used.  See the
    Django documentation for it's full syntax.

    Requesting this fixture will start a session wide live server.
    """
    skip_if_no_django()
    addr = request.config.getvalue('liveserver')
    if not addr:
        addr = os.getenv('DJANGO_TEST_LIVE_SERVER_ADDRESS')
    if not addr:
        addr = 'localhost:8081,8100-8200,9100-9200,10100-10200'
    server = LiveServer(addr)

    server.start()
    request.addfinalizer(server.stop)

    return server


@pytest.fixture(scope='function')
def live_server(live_server_session, django_db_transactional):
    """
    An instance of a live_server combined with database access.
    """
    return live_server_session
