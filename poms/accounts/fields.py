from poms.accounts.models import AccountClassifier, Account, AccountAttributeType, AccountType
from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.obj_attrs.filters import AttributeClassifierBaseField
from poms.obj_perms.filters import ObjectPermissionPrefetchFilter, ObjectPermissionFilter
from poms.users.filters import OwnerByMasterUserFilter


# TODO: add perms
class AccountClassifierField(AttributeClassifierBaseField):
    queryset = AccountClassifier.objects
    # filter_backends = [OwnerByMasterUserFilter]


class AccountClassifierRootField(FilteredPrimaryKeyRelatedField):
    queryset = AccountClassifier.objects.filter(parent__isnull=True)
    # filter_backends = [OwnerByMasterUserFilter]


class AccountAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = AccountAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class AccountTypeField(FilteredPrimaryKeyRelatedField):
    queryset = AccountType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]


class AccountField(FilteredPrimaryKeyRelatedField):
    queryset = Account.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionPrefetchFilter,
        ObjectPermissionFilter,
    ]
