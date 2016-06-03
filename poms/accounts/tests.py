from __future__ import unicode_literals

from rest_framework import status
from rest_framework.test import APITestCase

from poms.accounts.models import AccountAttributeType
from poms.common.tests import BaseApiWithPermissionTestCase


class AccountTypeApiTestCase(BaseApiWithPermissionTestCase, APITestCase):
    def setUp(self):
        super(AccountTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account-type/'
        self._url_object = '/api/v1/accounts/account-type/%s/'
        self._change_permission = 'change_accounttype'

    def _create_obj(self, name='acc'):
        return self.add_account_type(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account_type(name, 'a')


class AccountAttributeTypeApiTestCase(BaseApiWithPermissionTestCase, APITestCase):
    def setUp(self):
        super(AccountAttributeTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account-attribute-type/'
        self._url_object = '/api/v1/accounts/account-attribute-type/%s/'
        self._change_permission = 'change_accountattributetype'

    def _create_obj(self, name='acc'):
        return self.add_account_attribute_type(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account_attribute_type(name, 'a')

    def _make_new_data(self, value_type=AccountAttributeType.STRING, user_object_permissions=None,
                       group_object_permissions=None):
        data = super(AccountAttributeTypeApiTestCase, self)._make_new_data(
            user_object_permissions=user_object_permissions, group_object_permissions=group_object_permissions)
        data['value_type'] = value_type
        return data

    def _make_classifiers(self):
        n = self._make_name()
        uc = self._make_user_code(n)
        return [
            {
                "user_code": '1_%s' % uc,
                "name": '1_%s' % n,
                "children": [
                    {
                        "user_code": '11_%s' % uc,
                        "name": '11_%s' % n,
                        "children": [
                            {
                                "user_code": '111_%s' % uc,
                                "name": '111_%s' % n,
                            }
                        ]
                    },
                    {
                        "user_code": '12_%s' % uc,
                        "name": '12_%s' % n,
                    }
                ]
            },
            {
                "user_code": '2_%s' % uc,
                "name": '2_%s' % n,
                "children": [
                    {
                        "user_code": '22_%s' % uc,
                        "name": '22_%s' % n,
                        "children": []
                    }
                ]
            }
        ]

    def _make_new_data_with_classifiers(self, value_type=AccountAttributeType.CLASSIFIER,
                                        user_object_permissions=None, group_object_permissions=None):
        data = self._make_new_data(value_type=value_type, user_object_permissions=user_object_permissions,
                                   group_object_permissions=group_object_permissions)
        data['classifiers'] = self._make_classifiers()
        return data

    def test_add_classifier(self):
        data = self._make_new_data_with_classifiers()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_string_with_classifiers(self):
        data = self._make_new_data_with_classifiers(value_type=AccountAttributeType.STRING)
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['classifiers'], [])

    def test_update_classifier(self):
        data = self._make_new_data_with_classifiers()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data.copy()
        data['classifiers'] = self._make_classifiers()
        response = self._update('a', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_as_string_with_classifiers(self):
        data = self._make_new_data(value_type=AccountAttributeType.STRING)
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data.copy()
        data['classifiers'] = self._make_classifiers()
        response = self._update('a', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['classifiers'], [])

    def test_list_classifier(self):
        data = self._make_new_data_with_classifiers()
        response = self._add('a', data)
        data = response.data.copy()

        response = self._list('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        for obj in response.data['results']:
            pass

    def test_get_classifier(self):
        data = self._make_new_data_with_classifiers()
        response = self._add('a', data)
        data = response.data.copy()

        response = self._get('a', data['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AccountApiTestCase(BaseApiWithPermissionTestCase, APITestCase):
    def setUp(self):
        super(AccountApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account/'
        self._url_object = '/api/v1/accounts/account/%s/'
        self._change_permission = 'change_account'

        self.add_account_type('-', 'a')

    def _create_obj(self, name='acc'):
        return self.add_account(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account(name, 'a')
