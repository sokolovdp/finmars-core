from poms.accounts.models import AccountClassifier, Account, AccountAttributeType, AccountType
from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.filters import FieldObjectPermissionBackend
from poms.users.filters import OwnerByMasterUserFilter


class AccountClassifierField(AttributeClassifierBaseField):
    queryset = AccountClassifier.objects


# class AccountClassifierRootField(FilteredPrimaryKeyRelatedField):
#     queryset = AccountClassifier.objects.filter(parent__isnull=True)
#     # filter_backends = [OwnerByMasterUserFilter]


class AccountAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = AccountAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class AccountTypeField(FilteredPrimaryKeyRelatedField):
    queryset = AccountType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]


class AccountField(FilteredPrimaryKeyRelatedField):
    queryset = Account.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        FieldObjectPermissionBackend,
    ]
