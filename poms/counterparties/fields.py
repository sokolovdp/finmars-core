from poms.common.fields import UserCodeOrPrimaryKeyRelatedField
from poms.counterparties.models import (
    Counterparty,
    CounterpartyGroup,
    Responsible,
    ResponsibleGroup,
)
from poms.users.filters import OwnerByMasterUserFilter


class CounterpartyGroupDefault:
    requires_context = True

    def set_context(self, serializer_field):
        from poms.users.models import MasterUser

        self._master_user = MasterUser.objects.all().first()

    def __call__(self, serializer_field):
        from poms.users.models import EcosystemDefault

        self.set_context(serializer_field)
        self.ecosystem_defaults = EcosystemDefault.cache.get_cache(master_user_pk=self._master_user.pk)

        return self.ecosystem_defaults.counterparty_group


class CounterpartyGroupField(UserCodeOrPrimaryKeyRelatedField):
    queryset = CounterpartyGroup.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class CounterpartyDefault:
    requires_context = True

    def set_context(self, serializer_field):
        from poms.users.models import MasterUser

        # Only One Space per Scheme
        self._master_user = MasterUser.objects.all().first()

    def __call__(self, serializer_field):
        self.set_context(serializer_field)
        from poms.users.models import EcosystemDefault

        self.ecosystem_defaults = EcosystemDefault.cache.get_cache(master_user_pk=self._master_user.pk)

        return self.ecosystem_defaults.counterparty


class CounterpartyField(UserCodeOrPrimaryKeyRelatedField):
    queryset = Counterparty.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class ResponsibleGroupDefault:
    requires_context = True

    def set_context(self, serializer_field):
        from poms.users.models import MasterUser

        self._master_user = MasterUser.objects.all().first()

    def __call__(self, serializer_field):
        self.set_context(serializer_field)
        from poms.users.models import EcosystemDefault

        self.ecosystem_defaults = EcosystemDefault.cache.get_cache(master_user_pk=self._master_user.pk)

        return self.ecosystem_defaults.responsible_group


class ResponsibleGroupField(UserCodeOrPrimaryKeyRelatedField):
    queryset = ResponsibleGroup.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class ResponsibleDefault:
    requires_context = True

    def set_context(self, serializer_field):
        from poms.users.models import MasterUser

        self._master_user = MasterUser.objects.all().first()

    def __call__(self, serializer_field):
        from poms.users.models import EcosystemDefault

        self.set_context(serializer_field)
        self.ecosystem_defaults = EcosystemDefault.cache.get_cache(master_user_pk=self._master_user.pk)

        return self.ecosystem_defaults.responsible


class ResponsibleField(UserCodeOrPrimaryKeyRelatedField):
    queryset = Responsible.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]
