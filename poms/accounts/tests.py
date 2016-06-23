from __future__ import unicode_literals

from poms.accounts.models import AccountAttributeType, Account, AccountType, AccountClassifier
from poms.common.tests import BaseApiWithPermissionTestCase, BaseApiWithAttributesTestCase, \
    BaseAttributeTypeApiTestCase, \
    BaseApiWithTagsTestCase


class AccountTypeApiTestCase(BaseApiWithPermissionTestCase, BaseApiWithTagsTestCase):
    model = AccountType

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


class AccountApiTestCase(BaseApiWithPermissionTestCase, BaseApiWithAttributesTestCase, BaseApiWithTagsTestCase):
    model = Account

    def setUp(self):
        super(AccountApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account/'
        self._url_object = '/api/v1/accounts/account/%s/'
        self._change_permission = 'change_account'

        account_type_dummy = self.create_account_type('-', 'a')
        self.assign_perms(account_type_dummy, 'a', users=['a0', 'a1', 'a2'])

        at_simple = self.create_account_attribute_type('simple', 'a', value_type=AccountAttributeType.STRING)
        self.assign_perms(at_simple, 'a', groups=['g1'])

        at_classifier = self.create_account_attribute_type('classifier', 'a',
                                                           value_type=AccountAttributeType.CLASSIFIER,
                                                           classifiers=[{
                                                               'name': 'n1',
                                                               'children': [
                                                                   {'name': 'n11',},
                                                                   {'name': 'n12',},
                                                               ]
                                                           }, {
                                                               'name': 'n2',
                                                               'children': [
                                                                   {'name': 'n21',},
                                                                   {'name': 'n22',},
                                                               ]
                                                           }, ])
        self.assign_perms(at_classifier, 'a', groups=['g1'])

        at_classifier2 = self.create_account_attribute_type('classifier2', 'a',
                                                            value_type=AccountAttributeType.CLASSIFIER,
                                                            classifiers=[{
                                                                'name': 'n1',
                                                                'children': [
                                                                    {'name': 'n11',},
                                                                    {'name': 'n12',},
                                                                ]
                                                            }, ])
        self.assign_perms(at_classifier2, 'a', groups=['g1'])

        t1 = self.create_tag('t1', 'a', content_types=[Account])
        t2 = self.create_tag('t2', 'a', content_types=[Account])
        self.assign_perms(t2, 'a', groups=['g1'])

    def _create_obj(self, name='acc'):
        return self.create_account(name, 'a')

    def _get_obj(self, name='acc'):
        return self.get_account(name, 'a')

    def _make_new_data(self, **kwargs):
        acc_type = self.get_account_type('-', 'a')
        data = super(AccountApiTestCase, self)._make_new_data(type=acc_type.id, **kwargs)
        # data['type'] = self.get_account_type('-', 'a').id
        return data
