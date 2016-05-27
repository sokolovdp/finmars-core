from rest_framework.permissions import BasePermission

from poms.obj_perms.permissions import ObjectPermissionBase


class TransactionObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        member = request.user.member
        if member.is_superuser:
            return True
        p = lambda obj1: ObjectPermissionBase().simple_has_object_permission(member, 'GET', obj1)
        print('p(obj.portfolio) -> %s' % p(obj.portfolio))
        print('p(obj.account_position) -> %s' % p(obj.account_position))
        print('p(obj.account_cash) -> %s' % p(obj.account_cash))
        print('p(obj.account_interim) -> %s' % p(obj.account_interim))
        return p(obj.portfolio) and (p(obj.account_position) | p (obj.account_cash) | p(obj.account_interim))
