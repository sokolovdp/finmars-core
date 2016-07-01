from poms.accounts.models import AccountClassifier, Account, AccountAttributeType, AccountType
from poms.common.fields import PrimaryKeyRelatedFilteredField
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.users.filters import OwnerByMasterUserFilter


class AccountClassifierField(AttributeClassifierBaseField):
    queryset = AccountClassifier.objects


class AccountAttributeTypeField(PrimaryKeyRelatedFilteredField):
    queryset = AccountAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
    ]


# class AccountTypeField(FilteredPrimaryKeyRelatedField):
#     queryset = AccountType.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class AccountTypeField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = AccountType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


# class AccountField(FilteredPrimaryKeyRelatedField):
#     queryset = Account.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class AccountField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = Account.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
