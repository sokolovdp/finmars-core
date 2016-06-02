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

    # def _obj1(self):
    #     return self.get_account('acc1', 'a')

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
        obj = self.get_account(obj['name'], 'a')
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
        obj = self.get_account(obj['name'], 'a')
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
        # print(json.dumps(response.data, indent=2))
        self.client.logout()
        return response

    def _get(self, user):
        self.client.login(username=user, password=user)
        response = self.client.get(self._url_object % self._obj1.id, format='json')
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

    def _make_new_data(self, user_object_permissions=None, group_object_permissions=None):
        data = {
            'name': uuid.uuid4().hex,
            'user_code': Truncator(uuid.uuid4().hex).chars(25, truncate=''),
            'short_name': uuid.uuid4().hex,
            'public_name': uuid.uuid4().hex,
        }
        self._add_permissions(data, user_object_permissions, group_object_permissions)
        return data

    # def _make_patch_data(self):
    #     data = {
    #         'name': uuid.uuid4().hex,
    #     }
    #     return data
    #
    # def _make_update_data(self, user):
    #     response = self._get(user)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = response.data.copy()
    #     data['name'] = uuid.uuid4().hex
    #     return data
    #
    # def _test_add(self, user):
    #     self.client.login(username=user, password=user)
    #
    #     data = {
    #         'name': uuid.uuid4().hex,
    #         'user_code': Truncator(uuid.uuid4().hex).chars(25, truncate=''),
    #         'short_name': uuid.uuid4().hex,
    #         'public_name': uuid.uuid4().hex,
    #     }
    #
    #     response = self.client.post(self._url_list, data=data, format='json')
    #     print(json.dumps(response.data, indent=2))
    #     response_data = response.data
    #
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #
    #     granted_permissions = response_data['granted_permissions']
    #     self.assertEqual(set(granted_permissions), {self._change_permission, })
    #
    #     self.client.logout()
    #     return response
    #
    # def _test_add_perms(self, user):
    #     self.client.login(username=user, password=user)
    #
    #     users = ['a2']
    #     groups = ['g1']
    #     perms = [self._change_permission]
    #
    #     name = '%s' % uuid.uuid4().hex
    #     data = {
    #         'name': name,
    #         'user_code': Truncator(name).chars(25),
    #         'short_name': name,
    #         'public_name': name,
    #     }
    #
    #     user_object_permissions = []
    #     group_object_permissions = []
    #     # if perms is None:
    #     #     perms = [self._change_permission]
    #     for perm in perms:
    #         for user in users:
    #             member = self.get_member(user, 'a')
    #             user_object_permissions.append({"member": member.id, "permission": perm})
    #         for group in groups:
    #             group = self.get_group(group, 'a')
    #             group_object_permissions.append({"group": group.id, "permission": perm})
    #     data['user_object_permissions'] = user_object_permissions
    #     data['group_object_permissions'] = group_object_permissions
    #
    #     response = self.client.post(self._url_list, data=data, format='json')
    #     # print(json.dumps(response.data, indent=2))
    #     response_data = response.data
    #
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     granted_permissions = response_data['granted_permissions']
    #     self.assertEqual(set(granted_permissions), {self._change_permission, })
    #
    #     member_a = self.get_member('a', 'a')
    #     member_a2 = self.get_member('a2', 'a')
    #     group_g1 = self.get_group('g1', 'a')
    #     expected_user_object_permissions = [
    #         {"member": member_a2.id, "permission": self._change_permission},
    #         {"member": member_a.id, "permission": self._change_permission},
    #     ]
    #     expected_group_object_permissions = [
    #         {"group": group_g1.id, "permission": self._change_permission},
    #     ]
    #
    #     six.assertCountEqual(self, response_data['user_object_permissions'], expected_user_object_permissions)
    #     six.assertCountEqual(self, response_data['group_object_permissions'], expected_group_object_permissions)
    #
    #     acc = self.get_account(data['name'], 'a')
    #     user_object_permissions = [{"member": o.member_id, "permission": o.permission.codename}
    #                                for o in acc.user_object_permissions.all()]
    #     six.assertCountEqual(self, user_object_permissions, expected_user_object_permissions)
    #
    #     group_object_permissions = [{"group": o.group_id, "permission": o.permission.codename}
    #                                 for o in acc.group_object_permissions.all()]
    #     six.assertCountEqual(self, group_object_permissions, expected_group_object_permissions)
    #
    #     self.client.logout()
    #     return response.data
    #
    # def _test_put(self, user, status_code=status.HTTP_200_OK):
    #     self.client.login(username=user, password=user)
    #
    #     response = self.client.get(self._url_object % self._obj1.id, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     data = response.data
    #     # print(json.dumps(data, indent=2))
    #
    #     data['name'] = '%s' % uuid.uuid4()
    #     response = self.client.put(self._url_object % self._obj1.id, data=data, format='json')
    #     # print(json.dumps(response.data, indent=2))
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['name'], data['name'])
    #
    #     self.client.logout()
    #     return response.data
    #
    # def _test_patch(self, user, status_code=status.HTTP_200_OK):
    #     self.client.login(username=user, password=user)
    #
    #     data = {
    #         'name': '%s' % uuid.uuid4(),
    #     }
    #     response = self.client.patch(self._url_object % self._obj1.id, data=data, format='json')
    #     # print(json.dumps(response.data, indent=2))
    #
    #     self.assertEqual(response.status_code, status_code)
    #     if status_code == status.HTTP_200_OK:
    #         self.assertEqual(response.data['name'], data['name'])
    #
    #     self.client.logout()
    #     return response.data
    #
    # def _test_delete(self, user, status_code=status.HTTP_204_NO_CONTENT):
    #     self.client.login(username=user, password=user)
    #
    #     response = self.client.delete(self._url_object % self._obj1.id)
    #     # print(response.status_code)
    #
    #     self.assertEqual(response.status_code, status_code)
    #
    #     self.client.logout()

    def test_list_by_owner(self):
        response = self._list('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        for obj in response.data['results']:
            # self.assertTrue('granted_permissions' in obj)
            self._check_granted_permissions(obj, expected=[])
            self.assertTrue('user_object_permissions' in obj)
            self.assertTrue('group_object_permissions' in obj)

    def test_list_by_admin(self):
        response = self._list('a0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        for obj in response.data['results']:
            # self.assertTrue('granted_permissions' in obj)
            self._check_granted_permissions(obj, expected=[])
            self.assertTrue('user_object_permissions' in obj)
            self.assertTrue('group_object_permissions' in obj)

    def test_list_by_a1(self):
        response = self._list('a1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        for obj in response.data['results']:
            # self.assertTrue('granted_permissions' in obj)
            self._check_granted_permissions(obj, expected=[self._change_permission])
            self.assertFalse('user_object_permissions' in obj)
            self.assertFalse('group_object_permissions' in obj)

    def test_list_by_a2(self):
        response = self._list('a2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_by_owner(self):
        response = self._get('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        # self.assertTrue('granted_permissions' in obj)
        self._check_granted_permissions(obj, expected=[])
        self.assertTrue('user_object_permissions' in obj)
        self.assertTrue('group_object_permissions' in obj)

    def test_get_by_admin(self):
        response = self._get('a0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        # self.assertTrue('granted_permissions' in obj)
        self._check_granted_permissions(obj, expected=[])
        self.assertTrue('user_object_permissions' in obj)
        self.assertTrue('group_object_permissions' in obj)

    def test_get_by_a1(self):
        response = self._get('a1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        # self.assertTrue('granted_permissions' in obj)
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self.assertFalse('user_object_permissions' in obj)
        self.assertFalse('group_object_permissions' in obj)

    def test_get_by_a2(self):
        response = self._get('a2')
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

    def test_update_without_permissions(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data.copy()

        data['name'] = uuid.uuid4().hex
        response = self._update('a1', data['id'], data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self._delete('a', response.data['id'])
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_without_permissions(self):
        data = self._make_new_data()
        response = self._add('a', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self._delete('a1', response.data['id'])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


    def test_delete_without_delete_permissions(self):
        data = self._make_new_data()
        response = self._add('a1', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self._delete('a1', response.data['id'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
