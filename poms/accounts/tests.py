from __future__ import unicode_literals

import uuid

from django.utils.text import Truncator
from rest_framework import status

from poms.accounts.models import Account
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

    def _make_new_data(self, user_object_permissions=None, group_object_permissions=None):
        data = {
            'name': uuid.uuid4().hex,
            'user_code': Truncator(uuid.uuid4().hex).chars(25, truncate=''),
            'short_name': uuid.uuid4().hex,
            'public_name': uuid.uuid4().hex,
        }
        self._add_permissions(data, user_object_permissions, group_object_permissions)
        return data

    def _create_list_data(self):
        Account.objects.all().delete()
        self.add_account('acc', 'a')
        acc = self.add_account('acc_with_user', 'a')
        self.assign_perms(acc, 'a', users=['a1', 'a2'])
        acc = self.add_account('acc_with_group', 'a')
        self.assign_perms(acc, 'a', groups=['g1'])

    def test_list_by_owner(self):
        self._create_list_data()
        response = self._list('a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        for obj in response.data['results']:
            # self.assertTrue('granted_permissions' in obj)
            self._check_granted_permissions(obj, expected=[])
            self.assertTrue('user_object_permissions' in obj)
            self.assertTrue('group_object_permissions' in obj)

    def test_list_by_admin(self):
        self._create_list_data()
        response = self._list('a0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        for obj in response.data['results']:
            # self.assertTrue('granted_permissions' in obj)
            self._check_granted_permissions(obj, expected=[])
            self.assertTrue('user_object_permissions' in obj)
            self.assertTrue('group_object_permissions' in obj)

    def test_list_by_a1(self):
        self._create_list_data()
        response = self._list('a1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        for obj in response.data['results']:
            # self.assertTrue('granted_permissions' in obj)
            self._check_granted_permissions(obj, expected=[self._change_permission])
            self.assertFalse('user_object_permissions' in obj)
            self.assertFalse('group_object_permissions' in obj)

    def test_list_by_a2(self):
        self._create_list_data()
        response = self._list('a2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_get_by_owner(self):
        acc = self.add_account('acc', 'a')
        response = self._get('a', acc.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        # self.assertTrue('granted_permissions' in obj)
        self._check_granted_permissions(obj, expected=[])
        self.assertTrue('user_object_permissions' in obj)
        self.assertTrue('group_object_permissions' in obj)

    def test_get_by_admin(self):
        acc = self.add_account('acc', 'a')
        response = self._get('a', acc.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        # self.assertTrue('granted_permissions' in obj)
        self._check_granted_permissions(obj, expected=[])
        self.assertTrue('user_object_permissions' in obj)
        self.assertTrue('group_object_permissions' in obj)

    def test_get_by_user(self):
        acc = self.add_account('acc_with_user', 'a')
        self.assign_perms(acc, 'a', users=['a1'])
        response = self._get('a1', acc.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        # self.assertTrue('granted_permissions' in obj)
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self.assertFalse('user_object_permissions' in obj)
        self.assertFalse('group_object_permissions' in obj)

    def test_get_by_group(self):
        acc = self.add_account('acc_with_user', 'a')
        self.assign_perms(acc, 'a', groups=['g1'])
        response = self._get('a1', acc.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        obj = response.data
        # self.assertTrue('granted_permissions' in obj)
        self._check_granted_permissions(obj, expected=[self._change_permission])
        self.assertFalse('user_object_permissions' in obj)
        self.assertFalse('group_object_permissions' in obj)

    def test_get_without_permission(self):
        acc = self.add_account('acc_with_user', 'a')
        self.assign_perms(acc, 'a', groups=['g1'])

        response = self._get('a2', acc.id)
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
        acc = self.add_account('acc', 'a')
        response = self._delete('a', acc.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_by_admin(self):
        acc = self.add_account('acc', 'a')
        response = self._delete('a0', acc.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_by_user(self):
        acc = self.add_account('acc', 'a')
        response = self._delete('a1', acc.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_not_found_by_user(self):
        acc = self.add_account('acc', 'a')
        response = self._delete('a1', acc.id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_without_delete_permission_by_user(self):
        acc = self.add_account('acc', 'a')
        self.assign_perms(acc, 'a', users=['a1'])
        response = self._delete('a1', acc.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_without_delete_permission_by_group(self):
        acc = self.add_account('acc', 'a')
        self.assign_perms(acc, 'a', groups=['g1'])
        response = self._delete('a1', acc.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
