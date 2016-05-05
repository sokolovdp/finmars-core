from poms.accounts.models import AccountClassifier, Account, AccountAttributeType, AccountType
from poms.common.fields import FilteredPrimaryKeyRelatedField
from poms.users.filters import OwnerByMasterUserFilter


class AccountClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = AccountClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class AccountClassifierRootField(FilteredPrimaryKeyRelatedField):
    queryset = AccountClassifier.objects.filter(parent__isnull=True)
    filter_backends = [OwnerByMasterUserFilter]


class AccountAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = AccountAttributeType.objects
    filter_backends = [OwnerByMasterUserFilter]


class AccountTypeField(FilteredPrimaryKeyRelatedField):
    queryset = AccountType.objects
    filter_backends = [OwnerByMasterUserFilter]


class AccountField(FilteredPrimaryKeyRelatedField):
    queryset = Account.objects
    filter_backends = [OwnerByMasterUserFilter]
