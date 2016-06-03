from __future__ import unicode_literals

from rest_framework.test import APITestCase

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
