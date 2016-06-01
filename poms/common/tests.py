from __future__ import unicode_literals, division, print_function

import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APITestCase

from poms.accounts.models import AccountType, Account
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentClass, InstrumentType, Instrument
from poms.obj_perms.utils import assign_perms
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.tags.models import Tag
from poms.users.models import MasterUser, Member, Group


class BaseTestCase(APITestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.add_master_user_complex('a', groups=['g1', 'g2'])
        self.add_master_user_complex('b', groups=['g1', 'g2'])

        self.add_user('a1')
        self.add_member(user='a1', master_user='a', groups=['g1'])
        self.add_user('a2')
        self.add_member(user='a2', master_user='a', groups=['g2'])

        self.add_user('b1')
        self.add_member(user='b1', master_user='b', groups=['g2'])

    def add_master_user_complex(self, name, groups):
        master_user = name
        self.add_master_user(master_user)

        self.add_group('-', master_user)
        if groups:
            for group in groups:
                self.add_group(group, master_user)

        user = name
        self.add_user(user)
        self.add_member(master_user, user, is_owner=True, is_admin=True)

        self.add_account_type('-', master_user)
        self.add_account('-', master_user, '-')
        self.add_counterparty('-', master_user)
        self.add_responsible('-', master_user)
        self.add_portfolio('-', master_user)
        self.add_instrument_type('-', master_user)
        self.add_instrument('-', master_user, instrument_type='-')

        self.add_strategy1('-', master_user)
        self.add_strategy2('-', master_user)
        self.add_strategy3('-', master_user)

        return master_user

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

    def add_group(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return Group.objects.create(master_user=master_user, name=name)

    def add_account_type(self, name, master_user):
        master_user = self.get_master_user(master_user)
        return AccountType.objects.create(master_user=master_user, name=name)

    def get_account_type(self, name, master_user):
        return AccountType.objects.get(name=name, master_user__name=master_user)

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

    def test_play1(self):
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
            'user_code':'acc3',
            'tags': [tag1.id, tag2.id]
        }, format='json')
        print('22 response', response)
        print('22 response.json', json.dumps(response.data, indent=2))
        client.logout()
