from __future__ import unicode_literals

from rest_framework import status

from poms.accounts.models import AccountAttributeType, Account, AccountType, AccountClassifier
from poms.common.tests import BaseApiWithPermissionTestCase, BaseApiWithAttributesTestCase, \
    BaseAttributeTypeApiTestCase, \
    BaseApiWithTagsTestCase
from poms.obj_perms.utils import get_perms_codename


class AccountTypeApiTestCase(BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase):
    model = AccountType
    ordering_fields = ['user_code', 'name', 'short_name', ]

    def setUp(self):
        super(AccountTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account-type/'
        self._url_object = '/api/v1/accounts/account-type/%s/'
        self._change_permission = 'change_accounttype'

    def _create_obj(self, name='acc'):
        return self.create_account_type(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account_type(name, 'a')


class AccountAttributeTypeApiTestCase(BaseAttributeTypeApiTestCase):
    model = AccountAttributeType
    classifier_model = AccountClassifier

    def setUp(self):
        super(AccountAttributeTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account-attribute-type/'
        self._url_object = '/api/v1/accounts/account-attribute-type/%s/'
        self._change_permission = 'change_accountattributetype'


class AccountApiTestCase(BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase, BaseApiWithAttributesTestCase):
    model = Account
    attribute_type_model = AccountAttributeType
    classifier_model = AccountClassifier

    def setUp(self):
        super(AccountApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account/'
        self._url_object = '/api/v1/accounts/account/%s/'
        self._change_permission = 'change_account'

        self.type_def = self.create_account_type('-', 'a')
        self.assign_perms(self.type_def, 'a', users=['a0', 'a1', 'a2'], groups=['g1', 'g2'],
                          perms=get_perms_codename(self.type_def, ['change', 'view']))

        self.type1 = self.create_account_type('type1', 'a')
        self.type2_a1 = self.create_account_type('type2_a1', 'a')
        self.assign_perms(self.type2_a1, 'a', users=['a1'], groups=[])
        self.type3_g2 = self.create_account_type('type3_g2', 'a')
        self.assign_perms(self.type3_g2, 'a', groups=['g2'])

    def _create_obj(self, name='acc'):
        return self.create_account(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account(name, 'a')

    def _make_new_data(self, **kwargs):
        account_type = self.get_account_type(kwargs.get('account_type', '-'), 'a')
        data = super(AccountApiTestCase, self)._make_new_data(type=account_type.id, **kwargs)
        return data

    def test_add_by_user_with_type_without_perms(self):
        data = self._make_new_data(account_type='type1')
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_by_group_with_type_without_perms(self):
        data = self._make_new_data(account_type='type1')
        response = self._add('a2', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
