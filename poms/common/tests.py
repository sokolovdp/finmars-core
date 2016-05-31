from __future__ import unicode_literals, division, print_function

import json

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from poms.currencies.models import Currency
from poms.users.models import MasterUser, Member, Group


class BaseTestCase(APITestCase):
    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.master_a = MasterUser.objects.create(name='a')
        self.ccy_a_def = Currency.objects.create(master_user=self.master_a, name=settings.CURRENCY_CODE)
        self.master_a.currency = self.ccy_a_def
        self.master_a.save()

        self.group_a_g1 = Group.objects.create(master_user=self.master_a, name='g1')
        self.group_a_g2 = Group.objects.create(master_user=self.master_a, name='g2')

        self.user_a = User.objects.create_user('a', password='a')
        self.member_a_a = Member.objects.create(master_user=self.master_a, user=self.user_a,
                                                is_owner=True, is_admin=True)

        self.user_a0 = User.objects.create_user('a0', password='a0')
        self.member_a0_a = Member.objects.create(master_user=self.master_a, user=self.user_a0,
                                                 is_owner=False, is_admin=True)

        self.user_a1 = User.objects.create_user('a1', password='a1')
        self.member_a1_a = Member.objects.create(master_user=self.master_a, user=self.user_a1,
                                                 is_owner=False, is_admin=False)
        self.member_a1_a.groups = [self.group_a_g1]

        self.user_a2 = User.objects.create_user('a2', password='a2')
        self.member_a2_a = Member.objects.create(master_user=self.master_a, user=self.user_a2,
                                                 is_owner=False, is_admin=False)
        self.member_a2_a.groups = [self.group_a_g2]

        # --------------------------------------------------------------------------------------------------------------

        self.user_b = User.objects.create_user('b', password='b')

        self.master_b = MasterUser.objects.create(name='b')
        self.ccy_b_def = Currency.objects.create(master_user=self.master_b, name=settings.CURRENCY_CODE)
        self.master_b.currency = self.ccy_b_def
        self.master_b.save()

        self.group_b_g1 = Group.objects.create(master_user=self.master_b, name='g1')

        self.member_b_b = Member.objects.create(master_user=self.master_b, user=self.user_b,
                                                is_owner=True, is_admin=True)

    def test_play1(self):
        client = self.client
        client.login(username='a', password='a')
        response = client.get('/api/v1/users/master-user/', format='json')

        print('2 response', response)
        print('2 response.json', json.dumps(response.data, indent=4))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        data = response.data['results']
        self.assertEqual(data[0], {
            "url": "http://testserver/api/v1/users/master-user/%s/" % self.master_a.id,
            "id": self.master_a.id,
            "name": "a",
            "currency": self.ccy_a_def.id,
            "language": "en",
            "timezone": "UTC",
            "is_current": True
        })

        client.logout()
