import string
import random

from django.conf import settings

from rapidsms.models import Backend, Contact, Connection
from rapidsms.tests.harness import backend
from rapidsms.log.mixin import LoggerMixin
from rapidsms.router import send, receive


__all__ = ('CustomRouter', 'MockBackendRouter', 'CreateDataTest')


class CreateDataTest(object, LoggerMixin):
    """
    Base test case that provides helper functions to create data
    """

    def random_string(self, length=255, extra_chars=''):
        chars = string.letters + extra_chars
        return ''.join([random.choice(chars) for i in range(length)])

    def create_backend(self, data={}):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        return Backend.objects.create(**defaults)

    def create_contact(self, data={}):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        return Contact.objects.create(**defaults)

    def create_connection(self, data={}):
        defaults = {
            'identity': self.random_string(10),
        }
        defaults.update(data)
        if 'backend' not in defaults:
            defaults['backend'] = self.create_backend()
        return Connection.objects.create(**defaults)


class CustomRouter(CreateDataTest):
    """
    Inheritable TestCase-like object that allows Router customization
    """
    router_class = 'rapidsms.router.blocking.BlockingRouter'
    backends = {}

    def _pre_rapidsms_setup(self):
        self._INSTALLED_BACKENDS = getattr(settings, 'INSTALLED_BACKENDS', {})
        setattr(settings, 'INSTALLED_BACKENDS', self.backends)
        self._RAPIDSMS_ROUTER = getattr(settings, 'RAPIDSMS_ROUTER', None)
        setattr(settings, 'RAPIDSMS_ROUTER', self.router_class)

    def _post_rapidsms_teardown(self):
        setattr(settings, 'INSTALLED_BACKENDS', self._INSTALLED_BACKENDS)
        setattr(settings, 'RAPIDSMS_ROUTER', self._RAPIDSMS_ROUTER)

    def __call__(self, result=None):
        self._pre_rapidsms_setup()
        super(CustomRouter, self).__call__(result)
        self._post_rapidsms_teardown()


class MockBackendRouter(CustomRouter):
    """
    Test exentions with BlockingRouter and MockBackend, and utility functions
    to examine outgoing messages
    """
    backends = {'mockbackend': {'ENGINE': backend.MockBackend}}

    def _post_rapidsms_teardown(self):
        super(MockBackendRouter, self)._post_rapidsms_teardown()
        self.clear()

    @property
    def outbox(self):
        return backend.outbox

    def clear(self):
        if hasattr(backend, 'outbox'):
            backend.outbox = []

    def receive(self, text, backend_name='mockbackend', identity=None,
                connection=None, fields=None):
        """receive wrapper to use mockbackend by default"""
        return receive(text, backend_name=backend_name, identity=identity,
                       connection=connection, fields=fields)

    def send(self, text, backend_name='mockbackend', identity=None,
             connection=None):
        """send wrapper to use mockbackend by default"""
        return send(text, backend_name=backend_name, identity=identity,
                    connection=connection)
