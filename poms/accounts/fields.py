from poms.accounts.models import AccountClassifier, Account
from poms.api.fields import FilteredPrimaryKeyRelatedField
from poms.users.filters import OwnerByMasterUserFilter


class AccountClassifierField(FilteredPrimaryKeyRelatedField):
    queryset = AccountClassifier.objects
    filter_backends = [OwnerByMasterUserFilter]


class AccountField(FilteredPrimaryKeyRelatedField):
    queryset = Account.objects
    filter_backends = [OwnerByMasterUserFilter]

