from __future__ import unicode_literals

import json
import uuid

import six
from django.utils.text import Truncator
from rest_framework import status

from poms.common.tests import BaseApiTestCase


class AccountApiTestCase(BaseApiTestCase):
    def setUp(self):
        super(AccountApiTestCase, self).setUp()

        self._url_list = '/api/v1/accounts/account/'
        self._url_object = '/api/v1/accounts/account/%s/'
        self._change_permission = 'change_account'

        # account = self.add_account('acc1', 'a')
        # self.assign_perms(account, 'a', groups=['g1'])

        self._obj1 = self.add_account('acc1', 'a')
        self.assign_perms(self._obj1, 'a', groups=['g1'])

        self._obj2_name = 'acc2'

    # def _obj1(self):
    #     return self.get_account('acc1', 'a')

    def _test_list(self, user, count):
        self.client.login(username=user, password=user)

        response = self.client.get(self._url_list, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], count)

        self.client.logout()

    def _test_add(self, user):
        self.client.login(username=user, password=user)

        data = {
            'name': uuid.uuid4().hex,
            'user_code': Truncator(uuid.uuid4().hex).chars(25, truncate=''),
            'short_name': uuid.uuid4().hex,
            'public_name': uuid.uuid4().hex,
        }

        response = self.client.post(self._url_list, data=data, format='json')
        print(json.dumps(response.data, indent=2))
        response_data = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        granted_permissions = response_data['granted_permissions']
        self.assertEqual(set(granted_permissions), {self._change_permission, })

        self.client.logout()
        return response.data

    def _test_add_perms(self, user):
        self.client.login(username=user, password=user)

        users = ['a2']
        groups = ['g1']
        perms = [self._change_permission]

        name = '%s' % uuid.uuid4().hex
        data = {
            'name': name,
            'user_code': Truncator(name).chars(25),
            'short_name': name,
            'public_name': name,
        }

        user_object_permissions = []
        group_object_permissions = []
        # if perms is None:
        #     perms = [self._change_permission]
        for perm in perms:
            for user in users:
                member = self.get_member(user, 'a')
                user_object_permissions.append({"member": member.id, "permission": perm})
            for group in groups:
                group = self.get_group(group, 'a')
                group_object_permissions.append({"group": group.id, "permission": perm})
        data['user_object_permissions'] = user_object_permissions
        data['group_object_permissions'] = group_object_permissions

        response = self.client.post(self._url_list, data=data, format='json')
        # print(json.dumps(response.data, indent=2))
        response_data = response.data

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        granted_permissions = response_data['granted_permissions']
        self.assertEqual(set(granted_permissions), {self._change_permission, })

        member_a = self.get_member('a', 'a')
        member_a2 = self.get_member('a2', 'a')
        group_g1 = self.get_group('g1', 'a')
        expected_user_object_permissions = [
            {"member": member_a2.id, "permission": self._change_permission},
            {"member": member_a.id, "permission": self._change_permission},
        ]
        expected_group_object_permissions = [
            {"group": group_g1.id, "permission": self._change_permission},
        ]

        six.assertCountEqual(self, response_data['user_object_permissions'], expected_user_object_permissions)
        six.assertCountEqual(self, response_data['group_object_permissions'], expected_group_object_permissions)

        acc = self.get_account(data['name'], 'a')
        user_object_permissions = [{"member": o.member_id, "permission": o.permission.codename}
                                   for o in acc.user_object_permissions.all()]
        six.assertCountEqual(self, user_object_permissions, expected_user_object_permissions)

        group_object_permissions = [{"group": o.group_id, "permission": o.permission.codename}
                                    for o in acc.group_object_permissions.all()]
        six.assertCountEqual(self, group_object_permissions, expected_group_object_permissions)

        self.client.logout()
        return response.data

    def _test_get(self, user, status_code=status.HTTP_200_OK):
        self.client.login(username=user, password=user)

        response = self.client.get(self._url_object % self._obj1.id, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status_code)

        self.client.logout()
        return response.data

    def _test_put(self, user, status_code=status.HTTP_200_OK):
        self.client.login(username=user, password=user)

        response = self.client.get(self._url_object % self._obj1.id, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        # print(json.dumps(data, indent=2))

        data['name'] = '%s' % uuid.uuid4()
        response = self.client.put(self._url_object % self._obj1.id, data=data, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], data['name'])

        self.client.logout()
        return response.data

    def _test_patch(self, user, status_code=status.HTTP_200_OK):
        self.client.login(username=user, password=user)

        data = {
            'name': '%s' % uuid.uuid4(),
        }
        response = self.client.patch(self._url_object % self._obj1.id, data=data, format='json')
        # print(json.dumps(response.data, indent=2))

        self.assertEqual(response.status_code, status_code)
        if status_code == status.HTTP_200_OK:
            self.assertEqual(response.data['name'], data['name'])

        self.client.logout()
        return response.data

    def _test_delete(self, user, status_code=status.HTTP_204_NO_CONTENT):
        self.client.login(username=user, password=user)

        response = self.client.delete(self._url_object % self._obj1.id)
        # print(response.status_code)

        self.assertEqual(response.status_code, status_code)

        self.client.logout()

    def test_owner_list(self):
        self._test_list('a', 2)

    def test_admin_list(self):
        self._test_list('a0', 2)

    def test_a1_list(self):
        self._test_list('a1', 1)

    def test_a2_list(self):
        self._test_list('a2', 0)

    def test_owner_add(self):
        self._test_add('a')

    def test_owner_add_with_perms(self):
        self._test_add_perms('a')

    def test_a1_add_perms(self):
        self._test_add_perms('a1')

    def test_owner_get(self):
        self._test_get('a')

    def test_a1_get(self):
        self._test_get('a1')

    def test_a2_get(self):
        self._test_get('a2', status_code=status.HTTP_404_NOT_FOUND)

    def test_owner_update(self):
        self._test_put('a')

    def test_a1_update(self):
        self._test_put('a1')

    def test_a2_partial_update(self):
        self._test_patch('a2', status_code=status.HTTP_404_NOT_FOUND)

    def test_owner_delete(self):
        self._test_delete('a')

    def test_a1_delete(self):
        self._test_delete('a1', status_code=status.HTTP_403_FORBIDDEN)

    def test_a2_delete(self):
        self._test_delete('a2', status_code=status.HTTP_404_NOT_FOUND)
