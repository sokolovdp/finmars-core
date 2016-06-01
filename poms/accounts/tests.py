from __future__ import unicode_literals

import six
from rest_framework import status

from poms.common.tests import BaseApiTestCase


class AccountApiTestCase(BaseApiTestCase):
    def setUp(self):
        super(AccountApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account/'
        self._url_object = '/api/v1/accounts/account/%s/'
        self._change_permission = 'change_account'

        account = self.add_account('acc1', 'a')
        self.assign_perms(account, 'a', groups=['g1'])

        # self._obj1 = self.get_account('acc1', 'a')
        # self.assign_perms(self._obj1, 'a', groups=['g1'])
        #
        # self._obj2_name = 'acc2'

    def _test_list_simple(self, user, count):
        self.client.login(username=user, password=user)

        response = self.client.get(self._url_list, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], count)

        self.client.logout()

    def _test_add(self, user, name, users=None, groups=None, perms=None):
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
                perms = [self._change_permission]
            if users:
                for user in users:
                    member = self.get_member(user, 'a')
                    for perm in perms:
                        user_object_permissions.append({"member": member.id, "permission": perm})
            if groups:
                for group in groups:
                    group = self.get_group(group, 'a')
                    for perm in perms:
                        group_object_permissions.append({"group": group.id, "permission": perm})
            data['user_object_permissions'] = user_object_permissions
            data['group_object_permissions'] = group_object_permissions

        response = self.client.post(self._url_list, data=data, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.logout()
        return response.data

    def _test_get(self, user, name, status_code=status.HTTP_200_OK):
        obj = self.get_account(name, 'a')

        self.client.login(username=user, password=user)

        response = self.client.get(self._url_object % obj.id, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status_code)

        self.client.logout()
        return response.data

    def _test_put(self, user, name, status_code=status.HTTP_200_OK):
        self.client.login(username=user, password=user)

        obj = self.get_account(name, 'a')

        response = self.client.get(self._url_object % obj.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # print(json.dumps(data, indent=2))

        data['name'] = '%s_v1' % obj.name
        response = self.client.put(self._url_object % obj.id, data=data, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], data['name'])

        self.client.logout()
        return response.data

    def _test_patch(self, user, name, status_code=status.HTTP_200_OK):
        self.client.login(username=user, password=user)

        obj = self.get_account(name, 'a')
        data = {}
        data['name'] = '%s_v1' % obj.name
        response = self.client.patch(self._url_object % obj.id, data=data, format='json')

        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status_code)
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data['name'], data['name'])

        self.client.logout()
        return response.data

    def _test_delete(self, user, name, status_code=status.HTTP_204_NO_CONTENT):
        self.client.login(username=user, password=user)

        obj = self.get_account(name, 'a')
        response = self.client.delete(self._url_object % obj.id)
        # print(response.status_code)

        self.assertEqual(response.status_code, status_code)

        self.client.logout()

    def test_owner_list(self):
        self._test_list_simple('a', 2)

    def test_admin_list(self):
        self._test_list_simple('a0', 2)

    def test_a1_list(self):
        self._test_list_simple('a1', 1)

    def test_a2_list(self):
        self._test_list_simple('a2', 0)

    def test_owner_add(self):
        self._test_add('a', 'acc2')

    def test_owner_add_with_perms(self):
        data = self._test_add('a', 'acc2', users=['a2'], groups=['g1'])

        user_object_permissions = data['user_object_permissions']
        group_object_permissions = data['group_object_permissions']

        member_a = self.get_member('a', 'a')
        member_a2 = self.get_member('a2', 'a')
        if six.PY3:
            self.assertCountEqual(user_object_permissions, [
                {"member": member_a2.id, "permission": self._change_permission},
                {"member": member_a.id, "permission": self._change_permission},
            ])

        group_g1 = self.get_group('g1', 'a')
        self.assertEqual(group_object_permissions, [
            {"group": group_g1.id, "permission": self._change_permission},
        ])

    def test_a1_add_perms(self):
        data = self._test_add('a1', 'acc2', users=['a2'], groups=['g1'])

        granted_permissions = data['granted_permissions']
        self.assertEqual(set(granted_permissions), {self._change_permission, })

    def test_owner_get(self):
        self._test_get('a', 'acc1')

    def test_a1_get(self):
        self._test_get('a1', 'acc1')

    def test_a2_get(self):
        self._test_get('a2', 'acc1', status_code=status.HTTP_404_NOT_FOUND)

    def test_owner_update(self):
        self._test_put('a', 'acc1')

    def test_a1_update(self):
        self._test_put('a1', 'acc1')

    def test_a2_update(self):
        self._test_patch('a2', 'acc1', status_code=status.HTTP_404_NOT_FOUND)

    def test_owner_delete(self):
        self._test_delete('a', 'acc1')

    def test_a1_delete(self):
        self._test_delete('a1', 'acc1', status_code=status.HTTP_403_FORBIDDEN)

    def test_a2_delete(self):
        self._test_delete('a2', 'acc1', status_code=status.HTTP_404_NOT_FOUND)
