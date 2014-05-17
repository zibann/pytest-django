import pytest

from ..lazy_django import skip_if_no_django


@pytest.fixture()
def rf():
    """RequestFactory instance"""
    skip_if_no_django()

    from django.test.client import RequestFactory

    return RequestFactory()


@pytest.fixture()
def client():
    """A Django test client instance"""
    skip_if_no_django()
    from django.test.client import Client
    return Client()


@pytest.fixture()
def admin_client(client, django_db):
    skip_if_no_django()

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
    except ImportError:
        from django.contrib.auth.models import User

    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@example.com', 'password')
        user.is_staff = True
        user.is_superuser = True
        user.save()

    client.login(username='admin', password='password')

    return client


class MonkeyPatchWrapper(object):
    def __init__(self, monkeypatch, wrapped_object):
        super(MonkeyPatchWrapper, self).__setattr__('monkeypatch', monkeypatch)
        super(MonkeyPatchWrapper, self).__setattr__('wrapped_object',
                                                    wrapped_object)

    def __getattr__(self, attr):
        return getattr(self.wrapped_object, attr)

    def __setattr__(self, attr, value):
        self.monkeypatch.setattr(self.wrapped_object, attr, value,
                                 raising=False)

    def __delattr__(self, attr):
        self.monkeypatch.delattr(self.wrapped_object, attr)


@pytest.fixture()
def settings(request, monkeypatch):
    """A Django settings object which restores changes after the testrun"""
    skip_if_no_django()

    from django.conf import settings as django_settings
    return MonkeyPatchWrapper(monkeypatch, django_settings)


def _validate_urls(marker):
    """This function validates the urls marker

    It checks the signature and creates the `urls` attribute on the
    marker which will have the correct value.
    """
    def apifun(urls):
        marker.urls = urls
    apifun(*marker.args, **marker.kwargs)


@pytest.fixture(autouse=True, scope='function')
def django_set_urlconf(request):
    """Apply the @pytest.mark.urls marker, internal to pytest-django"""
    marker = request.node.get_marker('urls')
    if marker:
        skip_if_no_django()
        import django.conf
        from django.core.urlresolvers import clear_url_caches

        _validate_urls(marker)
        original_urlconf = django.conf.settings.ROOT_URLCONF
        django.conf.settings.ROOT_URLCONF = marker.urls
        clear_url_caches()

        def restore():
            django.conf.settings.ROOT_URLCONF = original_urlconf

        request.addfinalizer(restore)
