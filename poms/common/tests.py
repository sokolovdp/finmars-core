from __future__ import unicode_literals, division, print_function

import json
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.text import Truncator
from rest_framework import status

from poms.accounts.models import AccountType, Account, AccountAttributeType
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentClass, InstrumentType, Instrument
from poms.obj_perms.utils import assign_perms
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.models import Tag
from poms.users.models import MasterUser, Member, Group


class BaseApiTestCase(object):
    def setUp(self):
        super(BaseApiTestCase, self).setUp()

        # self.add_master_user_complex('a', groups=['g1', 'g2'])
        # self.add_master_user_complex('b', groups=['g1', 'g2'])

        self.add_master_user('a')
        self.add_group('g1', 'a')
        self.add_group('g2', 'a')
        self.add_user('a')
        self.add_member(user='a', master_user='a', is_owner=True, is_admin=True)
        self.add_user('a0')
        self.add_member(user='a0', master_user='a', is_owner=False, is_admin=True)
        self.add_user('a1')
        self.add_member(user='a1', master_user='a', groups=['g1'])
        self.add_user('a2')
        self.add_member(user='a2', master_user='a', groups=['g2'])

        self.add_master_user('b')
        self.add_group('g1', 'b')
        self.add_group('g2', 'b')
        self.add_user('b')
        self.add_member(user='b', master_user='b', is_owner=True, is_admin=True)

    # def add_master_user_complex(self, name, groups):
    #     master_user = name
    #     self.add_master_user(master_user)
    #
    #     # self.add_group('-', master_user)
    #     if groups:
    #         for group in groups:
    #             self.add_group(group, master_user)
    #
    #     user = name
    #
    #     self.add_account_type('-', master_user)
    #     self.add_account('-', master_user, '-')
    #     self.add_counterparty('-', master_user)
    #     self.add_responsible('-', master_user)
    #     self.add_portfolio('-', master_user)
    #     self.add_instrument_type('-', master_user)
    #     self.add_instrument('-', master_user, instrument_type='-')
    #
    #     self.add_strategy1('-', master_user)
    #     self.add_strategy2('-', master_user)
    #     self.add_strategy3('-', master_user)
    #
    #     return master_user

    def add_master_user(self, name):
        master_user = MasterUser.objects.create(name=name)
        master_user.currency = Currency.objects.create(master_user=master_user, name=settings.CURRENCY_CODE)
        master_user.save()
        return master_user

    def get_master_user(self, name):
        return MasterUser.objects.get(name=name)

    def add_user(self, name):
        return User.objects.create_user(name, password=name)

    def get_user(self, name):
        return User.objects.get(username=name)

    def add_member(self, user, master_user, is_owner=False, is_admin=False, groups=None):
        master_user = self.get_master_user(master_user)
        user = self.get_user(user)
        member = Member.objects.create(master_user=master_user, user=user, is_owner=is_owner, is_admin=is_admin)
        if groups:
            member.groups = Group.objects.filter(master_user=master_user, name__in=groups)
        return member

    def get_member(self, user, master_user):
        return Member.objects.get(user__username=user, master_user__name=master_user)

    def add_group(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return Group.objects.create(master_user=master_user, name=name)

    def get_group(self, name, master_user):
        return Group.objects.get(name=name, master_user__name=master_user)

    def add_account_type(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return AccountType.objects.create(master_user=master_user, name=name)

    def get_account_type(self, name, master_user):
        return AccountType.objects.get(name=name, master_user__name=master_user)

    def add_account_attribute_type(self, name, master_user, value_type=AccountAttributeType.STRING):
        master_user = self.get_master_user(master_user)
        return AccountAttributeType.objects.create(master_user=master_user, name=name, value_type=value_type)

    def get_account_attribute_type(self, name, master_user):
        return AccountAttributeType.objects.get(name=name, master_user__name=master_user)

    def add_account(self, name, master_user, account_type='-'):
        account_type = self.get_account_type(account_type, master_user)
        master_user = self.get_master_user(master_user)
        return Account.objects.create(master_user=master_user, type=account_type, name=name)

    def get_account(self, name, master_user):
        return Account.objects.get(name=name, master_user__name=master_user)

    def add_counterparty(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return Counterparty.objects.create(master_user=master_user, name=name)

    def get_counterparty(self, name, master_user):
        return Counterparty.objects.get(name=name, master_user__name=master_user)

    def add_responsible(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return Responsible.objects.create(master_user=master_user, name=name)

    def get_responsible(self, name, master_user):
        return Responsible.objects.get(name=name, master_user__name=master_user)

    def add_portfolio(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return Portfolio.objects.create(master_user=master_user, name=name)

    def get_portfolio(self, name, master_user):
        return Portfolio.objects.get(name=name, master_user__name=master_user)

    def add_currency(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return Currency.objects.create(master_user=master_user, name=name)

    def get_currency(self, name, master_user):
        if name:
            return Currency.objects.get(name=name, master_user__name=master_user)
        else:
            master_user = self.get_master_user(master_user)
            return master_user.currency

    def add_instrument_type(self, name, master_user, instrument_class=None):
        master_user = self.get_master_user(master_user)
        instrument_class = instrument_class or InstrumentClass.objects.get(pk=InstrumentClass.GENERAL)
        return InstrumentType.objects.create(master_user=master_user, instrument_class=instrument_class, name=name)

    def get_instrument_type(self, name, master_user):
        return InstrumentType.objects.get(name=name, master_user__name=master_user)

    def add_instrument(self, name, master_user, instrument_type=None, pricing_currency=None, accrued_currency=None):
        instrument_type = self.get_instrument_type(name, master_user)
        pricing_currency = self.get_currency(pricing_currency, master_user)
        accrued_currency = self.get_currency(accrued_currency, master_user)
        master_user = self.get_master_user(master_user)
        return Instrument.objects.create(master_user=master_user, type=instrument_type, name=name,
                                         pricing_currency=pricing_currency, accrued_currency=accrued_currency)

    def get_instrument(self, name, master_user):
        return Instrument.objects.get(name=name, master_user__name=master_user)

    def add_strategy1(self, name, master_user, parent=None):
        parent = self.get_strategy1(parent, master_user) if parent else None
        master_user = self.get_master_user(master_user)
        return Strategy1.objects.create(master_user=master_user, name=name, parent=parent)

    def get_strategy1(self, name, master_user):
        return Strategy1.objects.get(name=name, master_user__name=master_user)

    def add_strategy2(self, name, master_user, parent=None):
        parent = self.get_strategy2(parent, master_user) if parent else None
        master_user = self.get_master_user(master_user)
        return Strategy2.objects.create(master_user=master_user, name=name, parent=parent)

    def get_strategy2(self, name, master_user):
        return Strategy2.objects.get(name=name, master_user__name=master_user)

    def add_strategy3(self, name, master_user, parent=None):
        parent = self.get_strategy3(parent, master_user) if parent else None
        master_user = self.get_master_user(master_user)
        return Strategy3.objects.create(master_user=master_user, name=name, parent=parent)

    def get_strategy3(self, name, master_user):
        return Strategy3.objects.get(name=name, master_user__name=master_user)

    def add_tag(self, name, master_user, content_types=None):
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
            # codename_set = ['view_%(model_name)s', 'change_%(model_name)s', 'manage_%(model_name)s']
            codename_set = ['change_%(model_name)s']
            kwargs = {
                'app_label': obj._meta.app_label,
                'model_name': obj._meta.model_name
            }
            perms = {perm % kwargs for perm in codename_set}
        assign_perms(obj, members=members, groups=groups, perms=perms)

    def _dump(self, data):
        print(json.dumps(data, indent=2))

    def _test_play1(self):
        master_user = self.get_master_user('a')

        client = self.client
        client.login(username='a', password='a')
        response = client.get('/api/v1/users/master-user/', format='json')
        print('response', response)
        print('response.json', json.dumps(response.data, indent=4))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        data = response.data['results']
        self.assertEqual(data[0], {
            "url": "http://testserver/api/v1/users/master-user/%s/" % master_user.id,
            "id": master_user.id,
            "name": "a",
            "currency": master_user.currency_id,
            "language": "en",
            "timezone": "UTC",
            "is_current": True
        })

        client.logout()

        account = self.add_account('acc2', 'a')
        self.assign_perms(account, 'a', groups=['g1'])

        client.login(username='a', password='a')
        response = client.get('/api/v1/accounts/account/', format='json')
        print('-  response', response)
        print('-  response.json', json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        client.logout()

        client.login(username='a1', password='a1')
        response = client.get('/api/v1/accounts/account/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        print('1  response', response)
        print('1  response.json', json.dumps(response.data, indent=2))
        response = client.get('/api/v1/accounts/account/%s/' % account.id, format='json')
        print('11 response', response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        client.logout()

        client.login(username='a2', password='a2')
        response = client.get('/api/v1/accounts/account/', format='json')
        print('2  response', response)
        print('2  response.json', json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        response = client.get('/api/v1/accounts/account/%s/' % account.id, format='json')
        print('21 response', response)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        tag1 = self.add_tag('tag1', 'a', [Account])
        self.assign_perms(tag1, 'a', groups=['g2'])
        tag2 = self.add_tag('tag2', 'a', [Account, AccountType])
        self.assign_perms(tag2, 'a', groups=['g2'])

        response = client.post('/api/v1/accounts/account/', data={
            'name': 'acc3',
            # 'user_code':'acc3',
            'tags': [tag1.id, tag2.id]
        }, format='json')
        print('22 response', response)
        print('22 response.json', json.dumps(response.data, indent=2))
        client.logout()


class BaseApiWithPermissionTestCase(BaseApiTestCase):
    def setUp(self):
        super(BaseApiWithPermissionTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account/'
        self._url_object = '/api/v1/accounts/account/%s/'
        self._change_permission = 'change_account'

        self._url_list = None
        self._url_object = None
        self._change_permission = None

        # self.add_account_type('-', 'a')

    def _create_obj(self, name='acc'):
        raise NotImplementedError()
        # return self.add_account(name, 'a')

    def _get_obj(self, name='acc'):
        raise NotImplementedError()
        # return self.get_account(name, 'a')

    def _create_list_data(self):
        self._create_obj('obj_root')
        obj = self._create_obj('obj_with_user')
        self.assign_perms(obj, 'a', users=['a1', 'a2'])
        obj = self._create_obj('obj_with_group')
        self.assign_perms(obj, 'a', groups=['g1'])

    def _make_name(self):
        return uuid.uuid4().hex

    def _make_user_code(self, name=None):
        if not name:
            name = uuid.uuid4().hex
        return Truncator(name).chars(20, truncate='')

    def _make_new_data(self, user_object_permissions=None, group_object_permissions=None):
        n = self._make_name()
        uc = self._make_user_code(n)
        data = {
            'name': n,
            'user_code': uc,
        }
        self._add_permissions(data, user_object_permissions, group_object_permissions)
        return data

    def _check_granted_permissions(self, obj, expected=None):
        self.assertTrue('granted_permissions' in obj)
        if expected is not None:
            self.assertEqual(set(expected), set(obj['granted_permissions']))

    def _check_user_object_permissions(self, obj, expected=None):
        self.assertTrue('user_object_permissions' in obj)
        if expected is not None:
            expected = [{
                            'member': self.get_member(e['user'], 'a').id,
                            'permission': e['permission']
                        }
                        for e in expected]
            actual = [dict(e) for e in obj['user_object_permissions']]
            self.assertEqual(expected, actual)

    def _check_group_object_permissions(self, obj, expected=None):
        self.assertTrue('group_object_permissions' in obj)
        if expected is not None:
            expected = [{
                            'group': self.get_group(e['group'], 'a').id,
                            'permission': e['permission']
                        }
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

    def _list(self, user):
        self.client.login(username=user, password=user)
        response = self.client.get(self._url_list, format='json')
        self.client.logout()
        return response

    def _get(self, user, id):
        self.client.login(username=user, password=user)
        response = self.client.get(self._url_object % id, format='json')
        self.client.logout()
        return response

    def _add(self, user, data):
        self.client.login(username=user, password=user)
        response = self.client.post(self._url_list, data=data, format='json')
        self.client.logout()
        return response

    def _update(self, user, id, data):
        self.client.login(username=user, password=user)
        response = self.client.put(self._url_object % id, data=data, format='json')
        self.client.logout()
        return response

    def _partial_update(self, user, id, data):
        self.client.login(username=user, password=user)
        response = self.client.patch(self._url_object % id, data=data, format='json')
        self.client.logout()
        return response

    def _delete(self, user, id):
        self.client.login(username=user, password=user)
        response = self.client.delete(self._url_object % id)
        self.client.logout()
        return response

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

    def test_list_by_owner(self):
        self._create_list_data()
        response = self._list('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        for obj in response.data['results']:
            self._check_granted_permissions(obj, expected=[])
            self.assertTrue('user_object_permissions' in obj)
            self.assertTrue('group_object_permissions' in obj)

    def test_list_by_admin(self):
        self._create_list_data()
        response = self._list('a0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        for obj in response.data['results']:
            self._check_granted_permissions(obj, expected=[])
            self.assertTrue('user_object_permissions' in obj)
            self.assertTrue('group_object_permissions' in obj)

    def test_list_by_a1(self):
        self._create_list_data()
        response = self._list('a1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        for obj in response.data['results']:
            self._check_granted_permissions(obj, expected=[self._change_permission])
            self.assertFalse('user_object_permissions' in obj)
            self.assertFalse('group_object_permissions' in obj)

    def test_list_by_a2(self):
        self._create_list_data()
        response = self._list('a2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_by_owner(self):
        obj = self._create_obj()
        response = self._get('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        self._check_granted_permissions(obj, expected=[])
        self.assertTrue('user_object_permissions' in obj)
        self.assertTrue('group_object_permissions' in obj)

    def test_get_by_admin(self):
        obj = self._create_obj()
        response = self._get('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        self._check_granted_permissions(obj, expected=[])
        self.assertTrue('user_object_permissions' in obj)
        self.assertTrue('group_object_permissions' in obj)

    def test_get_by_user(self):
        obj = self._create_obj()
        self.assign_perms(obj, 'a', users=['a1'])
        response = self._get('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self.assertFalse('user_object_permissions' in obj)
        self.assertFalse('group_object_permissions' in obj)

    def test_get_by_group(self):
        obj = self._create_obj()
        self.assign_perms(obj, 'a', groups=['g1'])
        response = self._get('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self.assertFalse('user_object_permissions' in obj)
        self.assertFalse('group_object_permissions' in obj)

    def test_get_without_permission(self):
        obj = self._create_obj()
        self.assign_perms(obj, 'a', groups=['g1'])
        response = self._get('a2', obj.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_by_owner(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self._check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission}])
        self._db_check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission}])
        self._check_group_object_permissions(obj, [])

    def test_add_by_admin(self):
        data = self._make_new_data()
        response = self._add('a0', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self._check_user_object_permissions(obj, [{'user': 'a0', 'permission': self._change_permission}])
        self._db_check_user_object_permissions(obj, [{'user': 'a0', 'permission': self._change_permission}])
        self._check_group_object_permissions(obj, [])

    def test_add_by_a1(self):
        data = self._make_new_data()
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self.assertFalse('user_object_permissions' in obj)
        self._db_check_user_object_permissions(obj, [{'user': 'a1', 'permission': self._change_permission}])
        self.assertFalse('group_object_permissions' in obj)

    def test_add_by_owner_with_additional_permissions(self):
        data = self._make_new_data(user_object_permissions=[{'user': 'a2', 'permission': self._change_permission}],
                                   group_object_permissions=[{'group': 'g1', 'permission': self._change_permission}])
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self._check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission},
                                                  {'user': 'a2', 'permission': self._change_permission}])
        self._db_check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission},
                                                     {'user': 'a2', 'permission': self._change_permission}])
        self._check_group_object_permissions(obj, [{'group': 'g1', 'permission': self._change_permission}])
        self._db_check_group_object_permissions(obj, [{'group': 'g1', 'permission': self._change_permission}])

    def test_add_by_admin_with_additional_permissions(self):
        data = self._make_new_data(user_object_permissions=[{'user': 'a2', 'permission': self._change_permission}],
                                   group_object_permissions=[{'group': 'g1', 'permission': self._change_permission}])
        response = self._add('a0', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self._check_user_object_permissions(obj, [{'user': 'a0', 'permission': self._change_permission},
                                                  {'user': 'a2', 'permission': self._change_permission}])
        self._db_check_user_object_permissions(obj, [{'user': 'a0', 'permission': self._change_permission},
                                                     {'user': 'a2', 'permission': self._change_permission}])
        self._check_group_object_permissions(obj, [{'group': 'g1', 'permission': self._change_permission}])
        self._db_check_group_object_permissions(obj, [{'group': 'g1', 'permission': self._change_permission}])

    def test_add_by_a1_with_additional_permissions(self):
        data = self._make_new_data(user_object_permissions=[{'user': 'a2', 'permission': self._change_permission}],
                                   group_object_permissions=[{'group': 'g1', 'permission': self._change_permission}])
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self._db_check_user_object_permissions(obj, [{'user': 'a1', 'permission': self._change_permission}])
        self._db_check_group_object_permissions(obj, [])

    def test_update_by_owner(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data.copy()

        data['name'] = uuid.uuid4().hex
        response = self._update('a', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self._check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission}])
        self._db_check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission}])
        self._check_group_object_permissions(obj, [])

    def test_update_by_a1(self):
        data = self._make_new_data()
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data.copy()

        data['name'] = uuid.uuid4().hex
        response = self._update('a1', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        obj = response.data
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self.assertFalse('user_object_permissions' in obj)
        self._db_check_user_object_permissions(obj, [{'user': 'a1', 'permission': self._change_permission}])
        self.assertFalse('group_object_permissions' in obj)

    def test_update_permissions_by_owner(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data.copy()

        data['name'] = uuid.uuid4().hex
        self._add_permissions(data,
                              user_object_permissions=[{'user': 'a', 'permission': self._change_permission},
                                                       {'user': 'a2', 'permission': self._change_permission}],
                              group_object_permissions=[{'group': 'g1', 'permission': self._change_permission}])
        response = self._update('a', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        self._check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission},
                                                  {'user': 'a2', 'permission': self._change_permission}])
        self._db_check_user_object_permissions(obj, [{'user': 'a', 'permission': self._change_permission},
                                                     {'user': 'a2', 'permission': self._change_permission}])
        self._check_group_object_permissions(obj, [{'group': 'g1', 'permission': self._change_permission}])
        self._db_check_group_object_permissions(obj, [{'group': 'g1', 'permission': self._change_permission}])

    def test_update_permissions_by_a1(self):
        data = self._make_new_data()
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data.copy()

        data['name'] = uuid.uuid4().hex
        self._add_permissions(data,
                              user_object_permissions=[{'user': 'a2', 'permission': self._change_permission}],
                              group_object_permissions=[{'group': 'g1', 'permission': self._change_permission}])
        response = self._update('a1', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        self._db_check_user_object_permissions(obj, [{'user': 'a1', 'permission': self._change_permission}])
        self._db_check_group_object_permissions(obj, [])

    def test_update_without_permission(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data.copy()

        data['name'] = uuid.uuid4().hex
        response = self._update('a1', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_by_owner(self):
        obj = self._create_obj()
        response = self._delete('a', obj.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_by_admin(self):
        obj = self._create_obj()
        response = self._delete('a0', obj.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_by_user(self):
        obj = self._create_obj()
        response = self._delete('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_not_found_by_user(self):
        obj = self._create_obj()
        response = self._delete('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_without_delete_permission_by_user(self):
        obj = self._create_obj()
        self.assign_perms(obj, 'a', users=['a1'])
        response = self._delete('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_without_delete_permission_by_group(self):
        obj = self._create_obj()
        self.assign_perms(obj, 'a', groups=['g1'])
        response = self._delete('a1', obj.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
