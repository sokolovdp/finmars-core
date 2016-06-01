from __future__ import unicode_literals

import json

from rest_framework import status

from poms.common.tests import BaseApiTestCase


class AccountApiTestCase(BaseApiTestCase):
    def setUp(self):
        super(AccountApiTestCase, self).setUp()

        account = self.add_account('acc1', 'a')
        self.assign_perms(account, 'a', groups=['g1'])

    def _list(self, user, count):
        # print('-'*79)
        # print('-> %s' % user)
        self.client.login(username=user, password=user)
        response = self.client.get('/api/v1/accounts/account/', format='json')
        # print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], count)
        self.client.logout()

    def _add(self, user, name, users=None, groups=None, perms=None):
        print('-' * 79)
        print('-> %s' % user)
        self.client.login(username=user, password=user)

        data = {
            'name': name,
            'user_code': name,
            'short_name': name,
            'public_name': name,
        }
        if users or groups:
            user_object_permissions = []
            group_object_permissions = []
            if perms is None:
                perms = ['change_account']
            if users:
                for user in users:
                    member = self.get_member(user, 'a')
                    for perm in perms:
                        user_object_permissions.append({
                            "member": member.id,
                            "permission": perm
                        })
            if groups:
                for group in groups:
                    group = self.get_group(group, 'a')
                    for perm in perms:
                        group_object_permissions.append({
                            "group": group.id,
                            "permission": perm
                        })
            data['user_object_permissions'] = user_object_permissions
            data['group_object_permissions'] = group_object_permissions
        response = self.client.post('/api/v1/accounts/account/', data=data, format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        return response.data

    def test_owner_list(self):
        self._list('a', 2)

    def test_admin_list(self):
        self._list('a0', 2)

    def test_a1_list(self):
        self._list('a1', 1)

    def test_a2_list(self):
        self._list('a2', 0)

    def test_owner_add(self):
        self._add('a', 'acc2')

    def test_owner_add_perms(self):
        self._add('a', 'acc2', users=['a2'], groups=['g1'])
