from __future__ import unicode_literals

from rest_framework import status

from poms.chats.models import ThreadStatus, Thread, Message, DirectMessage
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

    def _create_obj(self, subject='thread', status='-'):
        return self.create_thread(subject, 'a', status=status)

    def _get_obj(self, subject='thread'):
        return self.get_thread(subject, 'a')

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


class MessageApiTest(BaseApiTestCase):
    model = Message

    def setUp(self):
        super(MessageApiTest, self).setUp()

        self._url_list = '/api/v1/chats/message/'
        self._url_object = '/api/v1/chats/message/%s/'

        self.status_def = self.create_thread_status('-', 'a')
        self.thread1 = self.create_thread('-', 'a', '-')

    def _create_obj(self, text='thread_status', sender='a', thread='-'):
        return self.create_message(text, sender, 'a', thread)

    def _get_obj(self, text='thread_status'):
        return self.get_message(text, 'a')

    def _make_new_data(self, **kwargs):
        thread = self.get_thread(kwargs.get('thread', '-'), 'a')
        sender = self.get_member(kwargs.get('sender', 'a'), 'a')
        kwargs['thread'] = thread.id
        kwargs['sender'] = sender.id
        data = super(MessageApiTest, self)._make_new_data(**kwargs)
        data['text'] = data.pop('name')
        return data


class DirectMessageApiTest(BaseApiTestCase):
    model = DirectMessage

    def setUp(self):
        super(DirectMessageApiTest, self).setUp()

        self._url_list = '/api/v1/chats/direct-message/'
        self._url_object = '/api/v1/chats/direct-message/%s/'

    def _create_obj(self, text='text', sender='a', recipient='a0'):
        return self.create_direct_message(text, 'a', sender, recipient)

    def _get_obj(self, text='text'):
        return self.get_direct_message(text, 'a')

    def _make_new_data(self, **kwargs):
        sender = self.get_member(kwargs.get('sender', 'a'), 'a')
        recipient = self.get_member(kwargs.get('recipient', 'a'), 'a')
        kwargs['sender'] = sender.id
        kwargs['recipient'] = recipient.id
        data = super(DirectMessageApiTest, self)._make_new_data(**kwargs)
        data['text'] = data.pop('name')
        return data
