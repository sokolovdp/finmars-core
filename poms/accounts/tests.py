from __future__ import unicode_literals

from rest_framework.test import APITestCase

from poms.accounts.models import AccountAttributeType, AccountClassifier, Account, AccountType
from poms.common.tests import BaseApiWithPermissionTestCase, BaseApiWithAttributesTestCase, BaseAttributeTypeApiTestCase


class AccountTypeApiTestCase(BaseApiWithPermissionTestCase, APITestCase):
    model = AccountType

    def setUp(self):
        super(AccountTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account-type/'
        self._url_object = '/api/v1/accounts/account-type/%s/'
        self._change_permission = 'change_accounttype'

    def _create_obj(self, name='acc'):
        return self.add_account_type(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account_type(name, 'a')


class AccountAttributeTypeApiTestCase(BaseAttributeTypeApiTestCase):
    model = AccountAttributeType

    def setUp(self):
        super(AccountAttributeTypeApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account-attribute-type/'
        self._url_object = '/api/v1/accounts/account-attribute-type/%s/'
        self._change_permission = 'change_accountattributetype'

    def _create_obj(self, name='acc'):
        return self.add_account_attribute_type(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account_attribute_type(name, 'a')


class AccountApiTestCase(BaseApiWithPermissionTestCase, BaseApiWithAttributesTestCase, APITestCase):
    model = Account

    def setUp(self):
        super(AccountApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account/'
        self._url_object = '/api/v1/accounts/account/%s/'
        self._change_permission = 'change_account'

        account_type_dummy = self.add_account_type('-', 'a')
        self.assign_perms(account_type_dummy, 'a', users=['a0', 'a1', 'a2'])

        at_simple = self.add_account_attribute_type('simple', 'a', value_type=AccountAttributeType.STRING)
        self.assign_perms(at_simple, 'a', groups=['g1'])

        at_classifier = self.add_account_attribute_type('classifier', 'a', value_type=AccountAttributeType.CLASSIFIER)
        self.assign_perms(at_classifier, 'a', groups=['g1'])
        n1 = AccountClassifier.objects.create(attribute_type=at_classifier, name='n1')
        n11 = AccountClassifier.objects.create(attribute_type=at_classifier, name='n11', parent=n1)
        n12 = AccountClassifier.objects.create(attribute_type=at_classifier, name='n12', parent=n1)
        n2 = AccountClassifier.objects.create(attribute_type=at_classifier, name='n2')
        n21 = AccountClassifier.objects.create(attribute_type=at_classifier, name='n21', parent=n2)
        n22 = AccountClassifier.objects.create(attribute_type=at_classifier, name='n22', parent=n2)

        at_classifier2 = self.add_account_attribute_type('classifier2', 'a', value_type=AccountAttributeType.CLASSIFIER)
        self.assign_perms(at_classifier, 'a', groups=['g1'])
        n1 = AccountClassifier.objects.create(attribute_type=at_classifier2, name='n1')
        n11 = AccountClassifier.objects.create(attribute_type=at_classifier2, name='n11', parent=n1)
        n12 = AccountClassifier.objects.create(attribute_type=at_classifier2, name='n12', parent=n1)

        t1 = self.add_tag('t1', 'a', content_types=[Account])
        t2 = self.add_tag('t2', 'a', content_types=[Account])
        self.assign_perms(t2, 'a', groups=['g1'])

    def _create_obj(self, name='acc'):
        return self.add_account(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account(name, 'a')

    def _make_new_data(self, user_object_permissions=None, group_object_permissions=None):
        data = super(AccountApiTestCase, self)._make_new_data(user_object_permissions=user_object_permissions,
                                                              group_object_permissions=group_object_permissions)
        data['type'] = self.get_account_type('-', 'a').id
        return data
