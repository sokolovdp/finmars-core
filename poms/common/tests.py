from __future__ import unicode_literals, division, print_function

import json
import uuid

import six
from django.conf import settings
from django.contrib.auth import user_logged_in, user_logged_out
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.utils.text import Truncator
from rest_framework import status
from rest_framework.test import APITestCase

from poms.accounts.models import AccountType, Account, AccountAttributeType, AccountClassifier
from poms.counterparties.models import Counterparty, Responsible, CounterpartyAttributeType, ResponsibleAttributeType, \
    ResponsibleClassifier, CounterpartyClassifier
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentClass, InstrumentType, Instrument, InstrumentAttributeType, \
    InstrumentClassifier
from poms.obj_attrs.models import AttributeTypeBase
from poms.obj_perms.utils import assign_perms, get_all_perms, get_default_owner_permissions, get_perms_codename
from poms.portfolios.models import Portfolio, PortfolioAttributeType, PortfolioClassifier
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.models import Tag
from poms.users.models import MasterUser, Member, Group


def load_tests(loader, standard_tests, pattern):
    result = []
    abstract_tests = (
        BaseApiTestCase,
        BaseNamedModelTestCase,
        BaseApiWithPermissionTestCase,
        BaseApiWithAttributesTestCase,
        BaseApiWithTagsTestCase,
        BaseAttributeTypeApiTestCase,
    )
    for test_case in standard_tests:
        if type(test_case._tests[0]) in abstract_tests:
            continue
        result.append(test_case)
    return loader.suiteClass(result)


@receiver(user_logged_in, dispatch_uid='tests_user_logged_in')
def tests_user_logged_in(user=None, **kwargs):
    # print('user_logged_in: user=%s' % user)
    pass


@receiver(user_logged_out, dispatch_uid='tests_user_logged_out')
def tests_user_logged_out(user=None, **kwargs):
    # print('user_logged_out: user=%s' % user)
    pass


class BaseApiTestCase(APITestCase):
    model = None
    ordering_fields = None
    filtering_fields = None

    def __init__(self, *args, **kwargs):
        super(BaseApiTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        super(BaseApiTestCase, self).setUp()

        self._url_list = None
        self._url_object = None
        self._change_permission = None

        self.all_permissions = set(get_all_perms(self.model))
        self.default_owner_permissions = set([p.codename for p in get_default_owner_permissions(self.model)])

        self.create_master_user('a')
        self.create_group('g1', 'a')
        self.create_group('g2', 'a')
        self.create_user('a')
        self.create_member(user='a', master_user='a', is_owner=True, is_admin=True)
        self.create_user('a0')
        self.create_member(user='a0', master_user='a', is_owner=False, is_admin=True)
        self.create_user('a1')
        self.create_member(user='a1', master_user='a', groups=['g1'])
        self.create_user('a2')
        self.create_member(user='a2', master_user='a', groups=['g2'])

        self.create_master_user('b')
        self.create_group('g1', 'b')
        self.create_group('g2', 'b')
        self.create_user('b')
        self.create_member(user='b', master_user='b', is_owner=True, is_admin=True)

    def create_name(self):
        return uuid.uuid4().hex

    def create_user_code(self, name=None):
        if not name:
            name = uuid.uuid4().hex
        return Truncator(name).chars(20, truncate='')

    def create_master_user(self, name):
        master_user = MasterUser.objects.create(name=name)
        master_user.currency = Currency.objects.create(master_user=master_user, name=settings.CURRENCY_CODE)
        master_user.save()
        # print('create master user: id=%s, name=%s' %
        #       (master_user.id, name))
        return master_user

    def get_master_user(self, name):
        return MasterUser.objects.get(name=name)

    def create_user(self, name):
        return User.objects.create_user(name, password=name)

    def get_user(self, name):
        return User.objects.get(username=name)

    def create_member(self, user, master_user, is_owner=False, is_admin=False, groups=None):
        master_user = self.get_master_user(master_user)
        user = self.get_user(user)
        member = Member.objects.create(master_user=master_user, user=user, is_owner=is_owner, is_admin=is_admin)
        if groups:
            member.groups = Group.objects.filter(master_user=master_user, name__in=groups)
        # print('create member: id=%s, name=%s, master_user=%s, is_owner=%s, is_admin=%s, groups=%s' %
        #       (member.id, user, master_user, is_owner, is_admin, groups))
        return member

    def get_member(self, user, master_user):
        return Member.objects.get(user__username=user, master_user__name=master_user)

    def create_group(self, name, master_user):
        master_user = self.get_master_user(master_user)
        group = Group.objects.create(master_user=master_user, name=name)
        # print('create group: id=%s, name=%s, master_user=%s' %
        #       (group.id, name, master_user))
        return group

    def get_group(self, name, master_user):
        return Group.objects.get(name=name, master_user__name=master_user)

    def create_attribute_type(self, model, name, master_user, value_type=AttributeTypeBase.STRING,
                              classifier_model=None, classifier_tree=None):
        master_user = self.get_master_user(master_user)
        attribute_type = model.objects.create(master_user=master_user, name=name, value_type=value_type)
        if classifier_model and classifier_tree and value_type == AttributeTypeBase.CLASSIFIER:
            for root in classifier_tree:
                self.create_classifier(attribute_type, classifier_model, root, None)
        return attribute_type

    def create_classifier(self, attribute_type, model, node, parent):
        name = node['name']
        children = node.get('children', [])
        classifier = model.objects.create(attribute_type=attribute_type, name=name, parent=parent)
        for child in children:
            self.create_classifier(attribute_type, model, child, classifier)
        return classifier

    def get_classifier(self, attribute_type_model, name, master_user, classifier_model=None, classifier_name=None):
        attribute_type = self.get_attribute_type(attribute_type_model, name, master_user)
        classifier = classifier_model.objects.get(attribute_type=attribute_type, name=classifier_name)
        return classifier

    def get_attribute_type(self, model, name, master_user):
        return model.objects.get(name=name, master_user__name=master_user)

    def create_currency(self, name, master_user):
        master_user = self.get_master_user(master_user)
        currency = Currency.objects.create(master_user=master_user, name=name)
        return currency

    def get_currency(self, name, master_user):
        if name:
            return Currency.objects.get(name=name, master_user__name=master_user)
        else:
            master_user = self.get_master_user(master_user)
            return master_user.currency

    def create_account_type(self, name, master_user):
        master_user = self.get_master_user(master_user)
        account_type = AccountType.objects.create(master_user=master_user, name=name)
        return account_type

    def get_account_type(self, name, master_user):
        return AccountType.objects.get(name=name, master_user__name=master_user)

    def create_account_attribute_type(self, name, master_user, value_type=AttributeTypeBase.STRING,
                                      classifiers=None):
        return self.create_attribute_type(AccountAttributeType, name, master_user, value_type=value_type,
                                          classifier_model=AccountClassifier, classifier_tree=classifiers)

    def get_account_attribute_type(self, name, master_user):
        return self.get_attribute_type(AccountAttributeType, name, master_user)

    def create_account(self, name, master_user, account_type='-'):
        account_type = self.get_account_type(account_type, master_user)
        master_user = self.get_master_user(master_user)
        account = Account.objects.create(master_user=master_user, type=account_type, name=name)
        return account

    def get_account(self, name, master_user):
        return Account.objects.get(name=name, master_user__name=master_user)

    def create_counterparty(self, name, master_user):
        master_user = self.get_master_user(master_user)
        counterparty = Counterparty.objects.create(master_user=master_user, name=name)
        return counterparty

    def get_counterparty(self, name, master_user):
        return Counterparty.objects.get(name=name, master_user__name=master_user)

    # def create_counterparty_attribute_type(self, name, master_user, value_type=AttributeTypeBase.STRING,
    #                                        classifiers=None):
    #     return self.create_attribute_type(CounterpartyAttributeType, name, master_user, value_type=value_type,
    #                                       classifier_model=CounterpartyClassifier, classifier_tree=classifiers)

    # def get_counterparty_attribute_type(self, name, master_user):
    #     return self.get_attribute_type(CounterpartyAttributeType, name, master_user)

    def create_responsible(self, name, master_user):
        master_user = self.get_master_user(master_user)
        responsible = Responsible.objects.create(master_user=master_user, name=name)
        return responsible

    def get_responsible(self, name, master_user):
        return Responsible.objects.get(name=name, master_user__name=master_user)

    # def create_responsible_attribute_type(self, name, master_user, value_type=AttributeTypeBase.STRING,
    #                                       classifiers=None):
    #     return self.create_attribute_type(ResponsibleAttributeType, name, master_user, value_type=value_type,
    #                                       classifier_model=ResponsibleClassifier, classifier_tree=classifiers)

    # def get_responsible_attribute_type(self, name, master_user):
    #     return self.get_attribute_type(ResponsibleAttributeType, name, master_user)

    def create_portfolio(self, name, master_user):
        master_user = self.get_master_user(master_user)
        portfolio = Portfolio.objects.create(master_user=master_user, name=name)
        return portfolio

    def get_portfolio(self, name, master_user):
        return Portfolio.objects.get(name=name, master_user__name=master_user)

    # def create_portfolio_attribute_type(self, name, master_user, value_type=AttributeTypeBase.STRING,
    #                                     classifiers=None):
    #     return self.create_attribute_type(PortfolioAttributeType, name, master_user, value_type=value_type,
    #                                       classifier_model=PortfolioClassifier, classifier_tree=classifiers)

    # def get_portfolio_attribute_type(self, name, master_user):
    #     return self.get_attribute_type(PortfolioAttributeType, name, master_user)

    def create_instrument_type(self, name, master_user, instrument_class=None):
        master_user = self.get_master_user(master_user)
        instrument_class = instrument_class or InstrumentClass.objects.get(pk=InstrumentClass.GENERAL)
        instrument_type = InstrumentType.objects.create(master_user=master_user, instrument_class=instrument_class,
                                                        name=name)
        return instrument_type

    def get_instrument_type(self, name, master_user):
        return InstrumentType.objects.get(name=name, master_user__name=master_user)

    def create_instrument(self, name, master_user, instrument_type=None, pricing_currency=None, accrued_currency=None):
        instrument_type = self.get_instrument_type(name, master_user)
        pricing_currency = self.get_currency(pricing_currency, master_user)
        accrued_currency = self.get_currency(accrued_currency, master_user)
        master_user = self.get_master_user(master_user)
        instrument = Instrument.objects.create(master_user=master_user, type=instrument_type, name=name,
                                               pricing_currency=pricing_currency, accrued_currency=accrued_currency)
        return instrument

    def get_instrument(self, name, master_user):
        return Instrument.objects.get(name=name, master_user__name=master_user)

    # def create_instrument_attribute_type(self, name, master_user, value_type=AccountAttributeType.STRING,
    #                                      classifiers=None):
    #     return self.create_attribute_type(InstrumentAttributeType, name, master_user, value_type=value_type,
    #                                       classifier_model=InstrumentClassifier, classifier_tree=classifiers)

    # def get_instrument_attribute_type(self, name, master_user):
    #     return self.get_attribute_type(InstrumentAttributeType, name, master_user)

    def create_strategy(self, model, name, master_user, parent=None):
        parent = self.get_strategy(model, parent, master_user) if parent else None
        master_user = self.get_master_user(master_user)
        strategy = model.objects.create(master_user=master_user, name=name, parent=parent)
        return strategy

    def get_strategy(self, model, name, master_user):
        return model.objects.get(name=name, master_user__name=master_user)

    def create_strategy1(self, name, master_user, parent=None):
        return self.create_strategy(Strategy1, name, master_user, parent=parent)

    def get_strategy1(self, name, master_user):
        return self.get_strategy(Strategy1, name, master_user)

    def create_strategy2(self, name, master_user, parent=None):
        return self.create_strategy(Strategy2, name, master_user, parent=parent)

    def get_strategy2(self, name, master_user):
        return self.get_strategy(Strategy2, name, master_user)

    def create_strategy3(self, name, master_user, parent=None):
        return self.create_strategy(Strategy3, name, master_user, parent=parent)

    def get_strategy3(self, name, master_user):
        return self.get_strategy(Strategy3, name, master_user)

    def create_tag(self, name, master_user, content_types=None):
        master_user = self.get_master_user(master_user)
        tag = Tag.objects.create(master_user=master_user, name=name)
        if content_types:
            tag.content_types = [ContentType.objects.get_for_model(model) for model in content_types]
        return tag

    def get_tag(self, name, master_user):
        return Tag.objects.get(name=name, master_user__name=master_user)

    def assign_perms(self, obj, master_user, users=None, groups=None, perms=None):
        if users:
            members = Member.objects.filter(user__username__in=users, master_user__name=master_user)
        else:
            members = None
        if groups:
            groups = Group.objects.filter(name__in=groups, master_user__name=master_user)

        if perms is None:
            # # codename_set = ['view_%(model_name)s', 'change_%(model_name)s', 'manage_%(model_name)s']
            # codename_set = ['change_%(model_name)s']
            # kwargs = {
            #     'app_label': obj._meta.app_label,
            #     'model_name': obj._meta.model_name
            # }
            # perms = {perm % kwargs for perm in codename_set}
            perms = self.default_owner_permissions
        assign_perms(obj, members=members, groups=groups, perms=perms)

    def _dump(self, data):
        # pprint.pprint(data, width=40)
        print(json.dumps(data, indent=2, sort_keys=True))

    def _create_obj(self, name='acc'):
        raise NotImplementedError()
        # return self.create_account(name, 'a')

    def _get_obj(self, name='acc'):
        raise NotImplementedError()
        # return self.get_account(name, 'a')

    def _list(self, user, data=None):
        self.client.login(username=user, password=user)
        response = self.client.get(self._url_list, format='json', data=data)
        self.client.logout()
        return response

    def _list_order(self, user, field, count):
        response = self._list(user, data={'ordering': '%s' % field})
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'Failed ordering: field=%s' % field)
        self.assertEqual(response.data['count'], count, 'Failed ordering: field=%s' % field)

        response = self._list(user, data={'ordering': '-%s' % field})
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'Failed ordering: field=-%s' % field)
        self.assertEqual(response.data['count'], count, 'Failed ordering: field=-%s' % field)

    def _list_filter(self, user, field, value, count):
        response = self._list(user, data={field: value})
        self.assertEqual(response.status_code, status.HTTP_200_OK, 'Failed filtering: field=-%s' % field)
        self.assertEqual(response.data['count'], count, 'Failed filtering: field=-%s' % field)
        return response

    def _get(self, user, id):
        self.client.login(username=user, password=user)
        response = self.client.get(self._url_object % id, format='json')
        self.client.logout()
        return response

    def _log_response(self, response):
        # if response.status_code in (status.HTTP_400_BAD_REQUEST,):
        #     print('response: status_code=%s, data=%s' % (response.status_code, response.data))
        pass

    def _add(self, user, data):
        self.client.login(username=user, password=user)
        response = self.client.post(self._url_list, data=data, format='json')
        self.client.logout()
        self._log_response(response)
        return response

    def _update(self, user, id, data):
        self.client.login(username=user, password=user)
        response = self.client.put(self._url_object % id, data=data, format='json')
        self.client.logout()
        self._log_response(response)
        return response

    def _partial_update(self, user, id, data):
        self.client.login(username=user, password=user)
        response = self.client.patch(self._url_object % id, data=data, format='json')
        self.client.logout()
        self._log_response(response)
        return response

    def _delete(self, user, id):
        self.client.login(username=user, password=user)
        response = self.client.delete(self._url_object % id)
        self.client.logout()
        self._log_response(response)
        return response

    def _make_new_data(self, **kwargs):
        n = self.create_name()
        data = {
            'name': n,
        }
        data.update(kwargs)
        return data

    def test_list(self):
        self._create_obj('obj1')
        self._create_obj('obj2')
        self._create_obj('obj3')

        # owner
        response = self._list('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_get(self):
        obj = self._create_obj('obj1')

        # owner
        response = self._get('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update(self):
        obj = self._create_obj('obj1')

        response = self._get('a', obj.id)
        udata = response.data.copy()

        # create by owner
        udata['name'] = self.create_name()
        response = self._update('a', obj.id, udata)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete(self):
        only_change_perms = get_perms_codename(self.model, ['change'])

        obj = self._create_obj('obj_a')
        response = self._delete('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class BaseNamedModelTestCase(BaseApiTestCase):
    def test_list_ordering(self):
        self._create_obj('obj1')
        self._create_obj('obj2')
        self._create_obj('obj3')

        self._list_order('a', 'user_code', 3)
        self._list_order('a', 'name', 3)
        self._list_order('a', 'short_name', 3)

    def test_list_filtering(self):
        self._create_obj('obj1')
        self._create_obj('obj2')

        self._list_filter('a', 'user_code', 'obj1', 1)
        self._list_filter('a', 'name', 'obj1', 1)
        self._list_filter('a', 'short_name', 'obj1', 1)


class BaseApiWithPermissionTestCase(BaseApiTestCase):
    def setUp(self):
        super(BaseApiWithPermissionTestCase, self).setUp()

    def _create_list_data(self):
        self._create_obj('obj_root')
        obj = self._create_obj('obj_with_user')
        self.assign_perms(obj, 'a', users=['a1', 'a2'])
        obj = self._create_obj('obj_with_group')
        self.assign_perms(obj, 'a', groups=['g1'])

    def _make_new_data(self, user_object_permissions=None, group_object_permissions=None, **kwargs):
        data = super(BaseApiWithPermissionTestCase, self)._make_new_data(**kwargs)
        self._add_permissions(data, user_object_permissions, group_object_permissions)
        return data

    def _add_permissions(self, data, user_object_permissions, group_object_permissions):
        if user_object_permissions:
            data['user_object_permissions'] = [{
                                                   'member': self.get_member(e['user'], 'a').id,
                                                   'permission': e['permission']
                                               }
                                               for e in user_object_permissions]
        if group_object_permissions:
            data['group_object_permissions'] = [{
                                                    'group': self.get_group(e['group'], 'a').id,
                                                    'permission': e['permission']
                                                }
                                                for e in group_object_permissions]
        return data

    def _check_granted_permissions(self, obj, expected=None):
        self.assertTrue('granted_permissions' in obj)
        if expected is not None:
            self.assertEqual(set(expected), set(obj['granted_permissions']))

    def _check_user_object_permissions(self, obj, expected=None):
        self.assertTrue('user_object_permissions' in obj)
        if expected is not None:
            expected = [{'member': self.get_member(e['user'], 'a').id, 'permission': e['permission']}
                        for e in expected]
            actual = [dict(e) for e in obj['user_object_permissions']]
            self.assertEqual(expected, actual)

    def _check_group_object_permissions(self, obj, expected=None):
        self.assertTrue('group_object_permissions' in obj)
        if expected is not None:
            expected = [{'group': self.get_group(e['group'], 'a').id, 'permission': e['permission']}
                        for e in expected]
            actual = [dict(e) for e in obj['group_object_permissions']]
            self.assertEqual(expected, actual)

    def _db_check_user_object_permissions(self, obj, expected):
        obj = self._get_obj(obj['name'])
        perms = [{
                     'member': o.member_id,
                     'permission': o.permission.codename
                 }
                 for o in obj.user_object_permissions.all()]
        expected = [{
                        'member': self.get_member(e['user'], 'a').id,
                        'permission': e['permission']
                    }
                    for e in expected]
        self.assertEqual(expected, perms)

    def _db_check_group_object_permissions(self, obj, expected=None):
        obj = self._get_obj(obj['name'])
        perms = [{
                     'group': o.group_id,
                     'permission': o.permission.codename
                 }
                 for o in obj.group_object_permissions.all()]
        expected = [{
                        'group': self.get_group(e['group'], 'a').id,
                        'permission': e['permission']
                    }
                    for e in expected]
        self.assertEqual(expected, perms)

    def check_obj_list_perm(self, obj_list, granted_permissions, object_permissions):
        for obj in obj_list:
            self.check_obj_perm(obj, granted_permissions, object_permissions)

    def check_obj_perm(self, obj, granted_permissions, object_permissions):
        self._check_granted_permissions(obj, expected=granted_permissions)
        if object_permissions:
            self.assertTrue('user_object_permissions' in obj)
            self.assertTrue('group_object_permissions' in obj)
        else:
            self.assertFalse('user_object_permissions' in obj)
            self.assertFalse('group_object_permissions' in obj)

    def test_permissions_list(self):
        obj = self._create_obj('obj')
        obj_a1 = self._create_obj('obj_a1')
        self.assign_perms(obj_a1, 'a', users=['a1'], perms=self.default_owner_permissions)
        obj_g2 = self._create_obj('obj_g2')
        self.assign_perms(obj_g2, 'a', groups=['g2'], perms=self.default_owner_permissions)

        # owner
        response = self._list('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.check_obj_list_perm(response.data['results'], self.all_permissions, True)

        # admin
        response = self._list('a0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.check_obj_list_perm(response.data['results'], self.all_permissions, True)

        response = self._list('a1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.check_obj_list_perm(response.data['results'], self.default_owner_permissions, False)

        response = self._list('a2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.check_obj_list_perm(response.data['results'], self.default_owner_permissions, False)

    def test_permissions_get(self):
        obj = self._create_obj('obj')
        obj12 = self._create_obj('obj_a1')
        self.assign_perms(obj12, 'a', users=['a1'], groups=['g2'], perms=self.default_owner_permissions)

        # owner
        response = self._get('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_obj_perm(response.data, self.all_permissions, True)

        # admin
        response = self._get('a0', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_obj_perm(response.data, self.all_permissions, True)

        # restricted access
        response = self._get('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(six.iterkeys(response.data)),
                         {'url', 'id', 'public_name', 'display_name', 'granted_permissions'})

        # restricted access
        response = self._get('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(six.iterkeys(response.data)),
                         {'url', 'id', 'public_name', 'display_name', 'granted_permissions'})

        response = self._get('a', obj12.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_obj_perm(response.data, self.all_permissions, True)

        response = self._get('a1', obj12.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_obj_perm(response.data, self.default_owner_permissions, False)

        response = self._get('a2', obj12.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_obj_perm(response.data, self.default_owner_permissions, False)

    def test_permissions_add(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.check_obj_perm(response.data, self.all_permissions, True)

        data = self._make_new_data()
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.check_obj_perm(response.data, self.default_owner_permissions, False)

        # add with perms
        data = self._make_new_data(user_object_permissions=[{'user': 'a1', 'permission': self._change_permission}],
                                   group_object_permissions=[{'group': 'g2', 'permission': self._change_permission}])
        response_wperms = self._add('a0', data)
        self.assertEqual(response_wperms.status_code, status.HTTP_201_CREATED)
        self.check_obj_perm(response_wperms.data, self.all_permissions, True)

        # permitted
        response = self._get('a1', response_wperms.data['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self._get('a2', response_wperms.data['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permissions_update(self):
        obj = self._create_obj(self.create_name())
        response = self._get('a', obj.id)
        udata = response.data.copy()

        # create by owner
        udata['name'] = self.create_name()
        response = self._update('a', obj.id, udata)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_obj_perm(response.data, self.default_owner_permissions, True)

        # no permissions
        response = self._update('a1', obj.id, udata)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # update permissions
        udata['name'] = self.create_name()
        perm = get_perms_codename(obj, ['change'])[0]
        self._add_permissions(udata,
                              user_object_permissions=[{'user': 'a1', 'permission': perm}],
                              group_object_permissions=[{'group': 'g2', 'permission': perm}])
        response = self._update('a0', obj.id, udata)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.check_obj_perm(response.data, self.default_owner_permissions, True)

        # permitted
        udata['name'] = self.create_name()
        response = self._update('a1', obj.id, udata)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # permitted
        udata['name'] = self.create_name()
        response = self._update('a2', obj.id, udata)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permissions_delete(self):
        only_change_perms = get_perms_codename(self.model, ['change'])

        obj = self._create_obj('obj_a')
        response = self._delete('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        obj = self._create_obj('obj_a1')
        response = self._delete('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        obj = self._create_obj('obj_a2')
        response = self._delete('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # delete by user
        obj = self._create_obj('obj_a1_1')
        self.assign_perms(obj, 'a', users=['a1'], groups=['g2'], perms=self.default_owner_permissions)
        response = self._delete('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # delete by group
        obj = self._create_obj('obj_a2_1')
        self.assign_perms(obj, 'a', users=['a1'], groups=['g2'], perms=self.default_owner_permissions)
        response = self._delete('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # no delete permission
        obj = self._create_obj('obj_a1_2')
        self.assign_perms(obj, 'a', users=['a1'], groups=['g2'], perms=only_change_perms)
        response = self._delete('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # no delete permission
        obj = self._create_obj('obj_a2_2')
        self.assign_perms(obj, 'a', users=['a1'], groups=['g2'], perms=only_change_perms)
        response = self._delete('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BaseApiWithTagsTestCase(BaseApiTestCase):
    def setUp(self):
        super(BaseApiWithTagsTestCase, self).setUp()

        if self.model == Account:
            self.model2 = AccountType
        else:
            self.model2 = Account

        self.tag1 = self.create_tag('tag1', 'a', [self.model])

        self.tag2_a1 = self.create_tag('tag2', 'a', [self.model])
        self.assign_perms(self.tag2_a1, 'a', users=['a1'], perms=get_all_perms(self.tag1))

        self.tag3_g2 = self.create_tag('tag3', 'a', [self.model])
        self.assign_perms(self.tag3_g2, 'a', groups=['g2'], perms=get_all_perms(self.tag1))

        self.tag4_ctype2 = self.create_tag('tag5', 'a', [self.model2])
        self.assign_perms(self.tag4_ctype2, 'a', users=['a1'], groups=['g2'], perms=get_all_perms(self.tag1))

    def test_tags_list(self):
        obj = self._create_obj()
        self.assign_perms(obj, 'a', users=['a1'], groups=['g2'])
        obj.tags = [self.tag1, self.tag2_a1, self.tag3_g2]

        response = self._list('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(set(response.data['results'][0]['tags']), {self.tag1.id, self.tag2_a1.id, self.tag3_g2.id, })

        response = self._list('a0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(set(response.data['results'][0]['tags']), {self.tag1.id, self.tag2_a1.id, self.tag3_g2.id, })

        response = self._list('a1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(set(response.data['results'][0]['tags']), {self.tag2_a1.id})

        response = self._list('a2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(set(response.data['results'][0]['tags']), {self.tag3_g2.id, })

    def test_tags_get(self):
        obj = self._create_obj()
        self.assign_perms(obj, 'a', users=['a1'], groups=['g2'])
        obj.tags = [self.tag1, self.tag2_a1, self.tag3_g2]

        response = self._get('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['tags']), {self.tag1.id, self.tag2_a1.id, self.tag3_g2.id, })

        response = self._get('a0', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['tags']), {self.tag1.id, self.tag2_a1.id, self.tag3_g2.id, })

        response = self._get('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['tags']), {self.tag2_a1.id})

        response = self._get('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['tags']), {self.tag3_g2.id, })

    def test_tags_update(self):
        data = self._make_new_data(tags=[self.tag1.id])
        response = self._add('a', data)
        data = response.data.copy()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data['tags']), {self.tag1.id})

        udata = data.copy()
        udata['tags'] = {self.tag1.id, self.tag2_a1.id, self.tag3_g2.id, }
        response = self._update('a', data['id'], udata)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['tags']), {self.tag1.id, self.tag2_a1.id, self.tag3_g2.id, })

        self.assign_perms(self.model.objects.get(id=data['id']), 'a', users=['a1'], groups=['g2'],
                          perms=self.all_permissions)
        response = self._get('a1', data['id'])
        udata = response.data.copy()
        udata['tags'] = []
        response = self._update('a1', data['id'], udata)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data['tags']), 0)

        response = self._get('a0', data['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data['tags']), {self.tag1.id, self.tag3_g2.id, })

    def test_tags_with_incorrect_ctype(self):
        data_tags = {self.tag4_ctype2.id}
        data = self._make_new_data(tags=data_tags)
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = self._make_new_data(tags={self.tag1.id})
        response = self._add('a', data)
        data = response.data.copy()
        data['tags'] = {self.tag4_ctype2.id}
        response = self._update('a', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tags_filter(self):
        pass


class BaseAttributeTypeApiTestCase(BaseNamedModelTestCase, BaseApiWithPermissionTestCase):
    classifier_model = None

    def create_default_attrs(self):
        self.attr_str = self.create_attribute_type(self.model, 'str', 'a',
                                                   value_type=AttributeTypeBase.STRING)
        self.attr_num = self.create_attribute_type(self.model, 'num', 'a',
                                                   value_type=AttributeTypeBase.NUMBER)
        self.attr_date = self.create_attribute_type(self.model, 'date', 'a',
                                                    value_type=AttributeTypeBase.DATE)
        self.attr_clsfr1 = self.create_attribute_type(self.model, 'clsfr1', 'a',
                                                      value_type=AttributeTypeBase.CLASSIFIER,
                                                      classifier_model=self.classifier_model,
                                                      classifier_tree=[{
                                                          'name': 'clsfr1_n1',
                                                          'children': [
                                                              {'name': 'clsfr1_n11',},
                                                              {'name': 'clsfr1_n12',},
                                                          ]
                                                      }, {
                                                          'name': 'clsfr1_n2',
                                                          'children': [
                                                              {'name': 'clsfr1_n21',},
                                                              {'name': 'clsfr1_n22',},
                                                          ]
                                                      }, ])
        self.attr_clsfr2 = self.create_attribute_type(self.model, 'clsfr2', 'a',
                                                      value_type=AttributeTypeBase.CLASSIFIER,
                                                      classifier_model=self.classifier_model,
                                                      classifier_tree=[{
                                                          'name': 'clsfr2_n1',
                                                          'children': [
                                                              {'name': 'clsfr2_n11',},
                                                              {'name': 'clsfr2_n12',},
                                                          ]
                                                      }, {
                                                          'name': 'clsfr2_n2',
                                                          'children': [
                                                              {'name': 'clsfr2_n21',},
                                                              {'name': 'clsfr2_n22',},
                                                          ]
                                                      }, ])

    def _gen_classifiers(self):
        n = self.create_name()
        uc = self.create_user_code(n)
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

    def _make_new_data_with_classifiers(self, value_type=AttributeTypeBase.CLASSIFIER, **kwargs):
        data = self._make_new_data(value_type=value_type, **kwargs)
        data['classifiers'] = self._gen_classifiers()
        return data

    def _create_obj(self, name='acc'):
        return self.create_attribute_type(self.model, name, 'a',
                                          classifier_model=self.classifier_model)

    def _get_obj(self, name='acc'):
        return self.get_attribute_type(self.model, name, 'a')

    def test_classifiers_get(self):
        self.create_default_attrs()
        response = self._get('a', self.attr_clsfr1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['classifiers']), 2)

    def test_classifiers_add(self):
        data = self._make_new_data_with_classifiers()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['classifiers']), 2)

        # try create with classifier with other value type
        data = self._make_new_data_with_classifiers(value_type=AttributeTypeBase.STRING)
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['classifiers'], [])

    def test_classifiers_update(self):
        data = self._make_new_data(value_type=AttributeTypeBase.CLASSIFIER)
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['classifiers']), 0)

        data = response.data.copy()
        data['classifiers'] = self._gen_classifiers()
        response = self._update('a', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['classifiers']), 2)

        # try add classifier to other value type
        data = self._make_new_data(value_type=AttributeTypeBase.STRING)
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data.copy()
        data['classifiers'] = self._gen_classifiers()
        response = self._update('a', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['classifiers'], [])


class BaseApiWithAttributesTestCase(BaseApiTestCase):
    attribute_type_model = None
    classifier_model = None
    skip_classifier = False

    def setUp(self):
        super(BaseApiWithAttributesTestCase, self).setUp()

        self.attr_str = self.create_attribute_type(self.attribute_type_model, 'str', 'a',
                                                   value_type=AttributeTypeBase.STRING)
        self.attr_num = self.create_attribute_type(self.attribute_type_model, 'num', 'a',
                                                   value_type=AttributeTypeBase.NUMBER)
        self.attr_date = self.create_attribute_type(self.attribute_type_model, 'date', 'a',
                                                    value_type=AttributeTypeBase.DATE)
        self.attr_clsfr1 = self.create_attribute_type(self.attribute_type_model, 'clsfr1', 'a',
                                                      value_type=AttributeTypeBase.CLASSIFIER,
                                                      classifier_model=self.classifier_model,
                                                      classifier_tree=[{
                                                          'name': 'clsfr1_n1',
                                                          'children': [
                                                              {'name': 'clsfr1_n11',},
                                                              {'name': 'clsfr1_n12',},
                                                          ]
                                                      }, {
                                                          'name': 'clsfr1_n2',
                                                          'children': [
                                                              {'name': 'clsfr1_n21',},
                                                              {'name': 'clsfr1_n22',},
                                                          ]
                                                      }, ])
        self.attr_clsfr2 = self.create_attribute_type(self.attribute_type_model, 'clsfr2', 'a',
                                                      value_type=AttributeTypeBase.CLASSIFIER,
                                                      classifier_model=self.classifier_model,
                                                      classifier_tree=[{
                                                          'name': 'clsfr2_n1',
                                                          'children': [
                                                              {'name': 'clsfr2_n11',},
                                                              {'name': 'clsfr2_n12',},
                                                          ]
                                                      }, {
                                                          'name': 'clsfr2_n2',
                                                          'children': [
                                                              {'name': 'clsfr2_n21',},
                                                              {'name': 'clsfr2_n22',},
                                                          ]
                                                      }, ])

    def get_model_classifier(self, name, classifier_name=None):
        return self.get_classifier(self.attribute_type_model, name, 'a', classifier_model=self.classifier_model,
                                   classifier_name=classifier_name)

    def attr_value_key(self, value_type):
        if value_type == AttributeTypeBase.STRING:
            return 'value_string'
        elif value_type == AttributeTypeBase.NUMBER:
            return 'value_float'
        elif value_type == AttributeTypeBase.DATE:
            return 'value_date'
        elif value_type == AttributeTypeBase.CLASSIFIER:
            return 'classifier'
        else:
            self.fail('invalid value_type %s' % (value_type))

    def add_attr_value(self, data, attr, value):
        attribute_type = self.get_attribute_type(self.attribute_type_model, attr, 'a')
        attributes = data.get('attributes', [])
        attributes = [x for x in attributes if x['attribute_type'] != attribute_type.id]
        # if value is not None:
        value_key = self.attr_value_key(attribute_type.value_type)
        attributes.append({'attribute_type': attribute_type.id, value_key: value})
        data['attributes'] = attributes
        return data

    def assertAttrEqual(self, attr, expected, attributes):
        attribute_type = self.get_attribute_type(self.attribute_type_model, attr, 'a')
        attributes = [x for x in attributes if x['attribute_type'] == attribute_type.id]
        if not attributes:
            self.fail('attribute %s not founded' % attr)
        value_key = self.attr_value_key(attribute_type.value_type)
        self.assertEqual(expected, attributes[0][value_key])

    def _simple_attrs(self, attr, value1, value2):
        # create attr
        data = self._make_new_data()
        data = self.add_attr_value(data, attr, value1)
        response = self._add('a', data)
        data = response.data.copy()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['attributes']), 1)
        self.assertAttrEqual(attr, value1, response.data['attributes'])

        # update attr
        data2 = data.copy()
        data2 = self.add_attr_value(data2, attr, value2)
        response = self._update('a', data2['id'], data2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 1)
        self.assertAttrEqual(attr, value2, response.data['attributes'])

        # update with None (currently attr doesn't deleted)
        data3 = data.copy()
        data3 = self.add_attr_value(data3, attr, None)
        response = self._update('a', data3['id'], data3)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 1)

        # # delete attr
        # response = self._delete('a', data3['id'])
        # self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_attrs_str(self):
        self._simple_attrs('str', 'value1', 'value2')

    def test_attrs_num(self):
        self._simple_attrs('num', 123, 456)

    def test_attrs_date(self):
        self._simple_attrs('date', '2014-01-01', '2015-01-01')

    def test_attrs_clsfr(self):
        if self.skip_classifier:
            return
        classifier1 = self.get_model_classifier('clsfr1', 'clsfr1_n11')
        classifier2 = self.get_model_classifier('clsfr1', 'clsfr1_n21')
        self._simple_attrs('clsfr1', classifier1.id, classifier2.id)

    def test_attrs_2_attrs(self):
        data = self._make_new_data()
        data = self.add_attr_value(data, 'str', 'value1')
        response = self._add('a', data)
        data = response.data.copy()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['attributes']), 1)

        data1 = data.copy()
        data1 = self.add_attr_value(data1, 'num', 123)
        response = self._update('a', data1['id'], data1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 2)
        self.assertAttrEqual('str', 'value1', response.data['attributes'])
        self.assertAttrEqual('num', 123, response.data['attributes'])

        data2 = data.copy()
        data2 = self.add_attr_value(data2, 'num', None)
        response = self._update('a', data2['id'], data2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 2)
        self.assertAttrEqual('str', 'value1', response.data['attributes'])
        self.assertAttrEqual('num', None, response.data['attributes'])

    def test_attrs_with_perms(self):
        self.assign_perms(self.attr_num, 'a', users=['a1'], perms=get_all_perms(self.attribute_type_model))

        data = self._make_new_data()
        data = self.add_attr_value(data, 'str', 'value1')
        response = self._add('a', data)
        data = response.data.copy()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['attributes']), 1)

        self.assign_perms(self.model.objects.get(pk=data['id']), 'a', users=['a1'])

        # user see only attrs with types perms
        response = self._get('a1', data['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('attributes' in response.data)
        self.assertEqual(len(response.data['attributes']), 0)

        # user add attribute
        data2 = response.data.copy()
        data2 = self.add_attr_value(data2, 'num', 123)
        response = self._update('a1', data2['id'], data2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 1)

        # superuser see all attrs
        response = self._get('a', data['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 2)

        # user delete attribute
        data2 = response.data.copy()
        data2['attributes'] = []
        response = self._update('a1', data2['id'], data2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 0)

        # superuser see 1 attr
        response = self._get('a', data['id'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['attributes']), 1)

        # try update attrs without type perms
        data3 = data.copy()
        data3 = self.add_attr_value(data3, 'num', 123)
        response = self._update('a1', data3['id'], data3)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=six.text_type(response.data))
