from __future__ import unicode_literals

import json

import six
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
        # print('-' * 79)
        # print('-> %s' % user)
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
        # print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.logout()
        return response.data

    def _get(self, user, account, status_code=status.HTTP_200_OK):
        account_id = self.get_account(account, 'a').id
        self.client.login(username=user, password=user)
        response = self.client.get('/api/v1/accounts/account/%s/' % account_id, format='json')
        # print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status_code)
        self.client.logout()
        return response.data

    def _put(self, user, account, status_code=status.HTTP_200_OK):
        self.client.login(username=user, password=user)

        account_obj = self.get_account(account, 'a')

        response = self.client.get('/api/v1/accounts/account/%s/' % account_obj.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # print(json.dumps(data, indent=2))

        data['name'] = '%s_v1' % data['name']
        response = self.client.put('/api/v1/accounts/account/%s/' % account_obj.id, data=data, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], data['name'])

        self.client.logout()
        return response.data

    def _patch(self, user, account, status_code=status.HTTP_200_OK):
        self.client.login(username=user, password=user)

        account_obj = self.get_account(account, 'a')
        data = {
            'name': '%s_v1' % account_obj.name,
        }
        response = self.client.patch('/api/v1/accounts/account/%s/' % account_obj.id, data=data, format='json')

        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status_code)
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data['name'], data['name'])

        self.client.logout()
        return response.data

    def _delete(self, user, account, status_code=status.HTTP_204_NO_CONTENT):
        self.client.login(username=user, password=user)

        account_obj = self.get_account(account, 'a')
        response = self.client.delete('/api/v1/accounts/account/%s/' % account_obj.id)
        # print(response.status_code)

        self.assertEqual(response.status_code, status_code)

        self.client.logout()

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

    def test_owner_add_with_perms(self):
        data = self._add('a', 'acc2', users=['a2'], groups=['g1'])

        user_object_permissions = data['user_object_permissions']
        group_object_permissions = data['group_object_permissions']

        member_a = self.get_member('a', 'a')
        member_a2 = self.get_member('a2', 'a')
        if six.PY3:
            self.assertCountEqual(user_object_permissions, [
                {"member": member_a2.id, "permission": "change_account"},
                {"member": member_a.id, "permission": "change_account"},
            ])

        group_g1 = self.get_group('g1', 'a')
        self.assertEqual(group_object_permissions, [
            {"group": group_g1.id, "permission": "change_account"},
        ])

    def test_a1_add_perms(self):
        data = self._add('a1', 'acc2', users=['a2'], groups=['g1'])

        granted_permissions = data['granted_permissions']
        self.assertEqual(set(granted_permissions), {"change_account", })

    def test_owner_get(self):
        self._get('a', 'acc1')

    def test_a1_get(self):
        self._get('a1', 'acc1')

    def test_a2_get(self):
        self._get('a2', 'acc1', status_code=status.HTTP_404_NOT_FOUND)

    def test_owner_update(self):
        self._put('a', 'acc1')

    def test_a1_update(self):
        self._put('a1', 'acc1')

    def test_a2_update(self):
        self._patch('a2', 'acc1', status_code=status.HTTP_404_NOT_FOUND)

    def test_owner_delete(self):
        self._delete('a', 'acc1')

    def test_a1_delete(self):
        self._delete('a1', 'acc1', status_code=status.HTTP_403_FORBIDDEN)

    def test_a2_delete(self):
        self._delete('a2', 'acc1', status_code=status.HTTP_404_NOT_FOUND)
