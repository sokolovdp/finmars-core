from __future__ import unicode_literals

from rest_framework import status

from poms.chats.models import ThreadStatus, Thread
from poms.common.tests import BaseApiTestCase, BaseApiWithPermissionTestCase


def load_tests(loader, standard_tests, pattern):
    from poms.common.tests import load_tests as t
    return t(loader, standard_tests, pattern)


class ThreadStatusApiTestCase(BaseApiTestCase):
    model = ThreadStatus

    def setUp(self):
        super(ThreadStatusApiTestCase, self).setUp()

        self._url_list = '/api/v1/chats/thread-status/'
        self._url_object = '/api/v1/chats/thread-status/%s/'

    def _create_obj(self, name='thread_status'):
        return self.create_thread_status(name, 'a')

    def _get_obj(self, name='thread_status'):
        return self.get_thread_status(name, 'a')

    def test_permissions(self):
        obj = self._create_obj('obj')

        response = self._get('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.copy()
        response = self._get('a0', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._get('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._get('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self._update('a', obj.id, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._update('a0', obj.id, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # only superuser can change
        response = self._update('a1', obj.id, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self._update('a2', obj.id, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ThreadApiTestCase(BaseApiWithPermissionTestCase):
    model = Thread

    def setUp(self):
        super(ThreadApiTestCase, self).setUp()

        self._url_list = '/api/v1/chats/thread/'
        self._url_object = '/api/v1/chats/thread/%s/'
        self._change_permission = 'change_thread'

        self.status_def = self.create_thread_status('-', 'a')

    def _create_obj(self, name='thread', status='-'):
        return self.create_thread(name, 'a', status=status)

    def _get_obj(self, name='thread'):
        return self.get_thread(name, 'a')

    def _make_new_data(self, **kwargs):
        status = self.get_thread_status(kwargs.get('status', '-'), 'a')
        kwargs['status'] = status.id
        data = super(ThreadApiTestCase, self)._make_new_data(**kwargs)
        data['subject'] = data.pop('name')
        return data

    def test_permissions_get_not_visible(self):
        obj = self._create_obj('obj')

        response = self._get('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._get('a0', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._get('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self._get('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
