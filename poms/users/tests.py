from __future__ import unicode_literals

from rest_framework import status

from poms.common.tests import BaseApiTestCase
from poms.users.models import Group


def load_tests(loader, standard_tests, pattern):
    from poms.common.tests import load_tests as t
    return t(loader, standard_tests, pattern)


class LanguageApiTestCase(BaseApiTestCase):
    model = None

    def setUp(self):
        super(LanguageApiTestCase, self).setUp()
        self._url_list = '/api/v1/users/language/'
        self._url_object = '/api/v1/users/language/%s/'

    def test_list(self):
        # owner
        response = self._list(self._a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get(self):
        pass

    def test_add(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass


class TimezoneApiTestCase(BaseApiTestCase):
    model = None

    def setUp(self):
        super(TimezoneApiTestCase, self).setUp()
        self._url_list = '/api/v1/users/timezone/'
        self._url_object = '/api/v1/users/timezone/%s/'

    def test_list(self):
        # owner
        response = self._list(self._a)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get(self):
        pass

    def test_add(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass


class ExpressionApiTestCase(BaseApiTestCase):
    model = None

    def setUp(self):
        super(ExpressionApiTestCase, self).setUp()
        self._url_list = '/api/v1/utils/expression/'
        self._url_object = '/api/v1/utils/expression/'

    def test_list(self):
        pass

    def test_get(self):
        pass

    def test_add(self):
        data = {
            'is_eval': True,
            'expression': '2 + 2',
        }
        response = self._add(self._a, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'is_eval': True,
            'expression': 'a + 2',
            'names1': {
                'a': 1
            },
        }
        response = self._add(self._a, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'is_eval': True,
            'expression': 'a + 2',
            'names2': '{"a": 1}',
        }
        response = self._add(self._a, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self):
        pass

    def test_delete(self):
        pass


class GroupApiTestCase(BaseApiTestCase):
    model = Group

    def setUp(self):
        super(GroupApiTestCase, self).setUp()

        self._url_list = '/api/v1/users/group/'
        self._url_object = '/api/v1/users/group/%s/'

    def _create_obj(self, name='name'):
        return self.create_group(name, self._a)

    def _get_obj(self, name='name'):
        return self.get_group(name, self._a)

# TODO: make when join algorithm was ready
# class MemberApiTestCase(BaseApiTestCase):
#     model = Member
#
#     def setUp(self):
#         super(MemberApiTestCase, self).setUp()
#
#         self._url_list = '/api/v1/users/member/'
#         self._url_object = '/api/v1/users/member/%s/'
#
#         self._u1 = self.create_user(uuid.uuid4())
#
#     def _create_obj(self, name=None):
#         if name is None:
#             user = self._u1.username
#         else:
#             user = self.get_user(name)
#         return self.create_member(user.username, self._a)
#
#     def _get_obj(self, name=None):
#         if name is None:
#             user = self._u1.username
#         else:
#             user = self.get_user(name)
#         return self.get_member(user.username, self._a)
#
#     def _make_new_data(self, **kwargs):
#         kwargs.setdefault('content_type', '%s.%s' % (content_type.app_label, content_type.model,))
#         kwargs.setdefault('data', {'pos': 1, 'uuid': str(uuid.uuid4())})
#         return super(ListLayoutApiTestCase, self)._make_new_data(**kwargs)
