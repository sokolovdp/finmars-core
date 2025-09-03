import logging
import traceback

import django_filters
from django_filters.fields import Lookup
from django_filters.rest_framework import FilterSet
from rest_framework.decorators import action
from rest_framework.response import Response

from poms.accounts.models import Account, AccountType
from poms.common.filters import CharExactFilter, CharFilter, NoOpFilter
from poms.common.mixins import DestroyModelMixinExt
from poms.common.views import (
    AbstractModelViewSet,
    AbstractReadOnlyModelViewSet,
    AbstractViewSet,
)
from poms.counterparties.models import (
    Counterparty,
    CounterpartyGroup,
    Responsible,
    ResponsibleGroup,
)
from poms.currencies.models import Currency
from poms.instruments.models import Instrument, InstrumentType
from poms.portfolios.models import Portfolio
from poms.reports.models import BalanceReport, TransactionReport
from poms.strategies.models import (
    Strategy1,
    Strategy1Subgroup,
    Strategy2,
    Strategy2Subgroup,
    Strategy3,
    Strategy3Subgroup,
)
from poms.transactions.models import TransactionType, TransactionTypeGroup
from poms.ui.models import (
    Bookmark,
    ColorPalette,
    ColumnSortData,
    ComplexTransactionUserField,
    ConfigurationExportLayout,
    ContextMenuLayout,
    CrossEntityAttributeExtension,
    DashboardLayout,
    Draft,
    EditLayout,
    EntityTooltip,
    InstrumentUserField,
    ListLayout,
    MemberLayout,
    MobileLayout,
    PortalInterfaceAccessModel,
    TemplateLayout,
    TransactionUserField,
    UserInterfaceAccessModel,
)
from poms.ui.serializers import (
    BookmarkSerializer,
    ColorPaletteSerializer,
    ColumnSortDataSerializer,
    ComplexTransactionUserFieldSerializer,
    ConfigurationExportLayoutSerializer,
    ContextMenuLayoutSerializer,
    CrossEntityAttributeExtensionSerializer,
    DashboardLayoutLightSerializer,
    DashboardLayoutSerializer,
    DraftSerializer,
    EditLayoutSerializer,
    EntityTooltipSerializer,
    InstrumentUserFieldSerializer,
    ListLayoutLightSerializer,
    ListLayoutSerializer,
    MemberLayoutSerializer,
    MobileLayoutSerializer,
    PortalInterfaceAccessModelSerializer,
    TemplateLayoutSerializer,
    TransactionUserFieldSerializer,
    UserInterfaceAccessModelSerializer,
)
from poms.users.filters import OwnerByMasterUserFilter, OwnerByMemberFilter

_l = logging.getLogger("poms.ui")


class LayoutContentTypeFilter(django_filters.CharFilter):
    def filter(self, qs, value):
        if isinstance(value, Lookup):
            lookup = str(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_expr

        if value in ([], (), {}, None, ""):
            return qs

        if self.distinct:
            qs = qs.distinct()

        try:
            app_label, model = value.split(".", maxsplit=1)
        except ValueError:
            # skip on invalid value
            app_label = model = ""

        qs = self.get_method(qs)(
            **{
                "content_type__app_label": app_label,
                f"content_type__model__{lookup}": model,
            }
        )
        return qs


class PortalInterfaceAccessViewSet(AbstractReadOnlyModelViewSet):
    queryset = PortalInterfaceAccessModel.objects
    serializer_class = PortalInterfaceAccessModelSerializer
    pagination_class = None


class UserInterfaceAccessModelFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    role = CharFilter()
    user_code = CharFilter()
    configuration_code = CharFilter()

    class Meta:
        model = UserInterfaceAccessModel
        fields = []


class UserInterfaceAccessModelViewSet(AbstractModelViewSet):
    queryset = UserInterfaceAccessModel.objects.all()
    serializer_class = UserInterfaceAccessModelSerializer
    filter_class = UserInterfaceAccessModelFilterSet


class ComplexTransactionUserFieldFilterSet(FilterSet):
    id = NoOpFilter()

    configuration_code = CharFilter()
    name = CharFilter()
    user_code = CharFilter()

    class Meta:
        model = ComplexTransactionUserField
        fields = []


class ComplexTransactionUserFieldViewSet(AbstractModelViewSet):
    queryset = ComplexTransactionUserField.objects.select_related("master_user", "owner")
    serializer_class = ComplexTransactionUserFieldSerializer
    filter_class = ComplexTransactionUserFieldFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]

    @action(detail=False, methods=["get"], url_path="primary")
    def primary(self, request, pk=None, realm_code=None, space_code=None):
        from poms.configuration.models import Configuration

        active_configuration = Configuration.objects.get(is_primary=True)

        queryset = self.get_queryset().filter(configuration_code=active_configuration.configuration_code)

        page = self.paginator.post_paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)


class TransactionUserFieldFilterSet(FilterSet):
    id = NoOpFilter()

    configuration_code = CharFilter()
    name = CharFilter()
    user_code = CharFilter()

    class Meta:
        model = TransactionUserField
        fields = []


class TransactionUserFieldViewSet(AbstractModelViewSet):
    queryset = TransactionUserField.objects.select_related("master_user", "owner")
    serializer_class = TransactionUserFieldSerializer
    filter_class = TransactionUserFieldFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]

    @action(detail=False, methods=["get"], url_path="primary")
    def primary(self, request, pk=None, realm_code=None, space_code=None):
        from poms.configuration.models import Configuration

        active_configuration = Configuration.objects.get(is_primary=True)

        queryset = self.get_queryset().filter(configuration_code=active_configuration.configuration_code)

        page = self.paginator.post_paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)


class ColorPaletteFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    user_code = CharFilter()

    class Meta:
        model = ColorPalette
        fields = []


class ColorPaletteViewSet(AbstractModelViewSet):
    queryset = ColorPalette.objects.select_related("master_user")
    serializer_class = ColorPaletteSerializer
    filter_class = ColorPaletteFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class EntityTooltipFilterSet(FilterSet):
    id = NoOpFilter()
    content_type = LayoutContentTypeFilter()

    class Meta:
        model = EntityTooltip
        fields = []


class EntityTooltipViewSet(AbstractModelViewSet):
    queryset = EntityTooltip.objects.select_related("master_user")
    serializer_class = EntityTooltipSerializer
    filter_class = EntityTooltipFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class CrossEntityAttributeExtensionFilterSet(FilterSet):
    id = NoOpFilter()
    content_type = LayoutContentTypeFilter()

    class Meta:
        model = CrossEntityAttributeExtension
        fields = []


class CrossEntityAttributeExtensionViewSet(AbstractModelViewSet):
    queryset = CrossEntityAttributeExtension.objects.select_related("master_user")
    serializer_class = CrossEntityAttributeExtensionSerializer
    filter_class = CrossEntityAttributeExtensionFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class ColumnSortDataFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    user_code = CharExactFilter()
    column_key = CharFilter()
    is_common = django_filters.BooleanFilter()

    class Meta:
        model = ColumnSortData
        fields = []


class ColumnSortDataViewSet(AbstractModelViewSet):
    queryset = ColumnSortData.objects.select_related("member")
    serializer_class = ColumnSortDataSerializer
    filter_class = ColumnSortDataFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]


class InstrumentUserFieldFilterSet(FilterSet):
    id = NoOpFilter()
    configuration_code = CharFilter()
    name = CharFilter()
    user_code = CharFilter()

    class Meta:
        model = InstrumentUserField
        fields = []


class InstrumentUserFieldViewSet(AbstractModelViewSet):
    queryset = InstrumentUserField.objects.select_related("master_user", "owner")
    serializer_class = InstrumentUserFieldSerializer
    filter_class = InstrumentUserFieldFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]

    @action(detail=False, methods=["get"], url_path="primary")
    def primary(self, request, pk=None, realm_code=None, space_code=None):
        from poms.configuration.models import Configuration

        active_configuration = Configuration.objects.get(is_primary=True)

        queryset = self.get_queryset().filter(configuration_code=active_configuration.configuration_code)

        page = self.paginator.post_paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)


class TemplateLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    is_default = django_filters.BooleanFilter()
    name = CharFilter()
    type = CharFilter()

    class Meta:
        model = TemplateLayout
        fields = []


class TemplateLayoutViewSet(AbstractModelViewSet):
    queryset = TemplateLayout.objects.select_related("member")
    serializer_class = TemplateLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = TemplateLayoutFilterSet
    ordering_fields = [
        "name",
        "is_default",
    ]


class ContextMenuLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    user_code = CharFilter()
    type = CharFilter()

    class Meta:
        model = ContextMenuLayout
        fields = []


class ContextMenuLayoutViewSet(AbstractModelViewSet):
    queryset = ContextMenuLayout.objects.select_related("member")
    serializer_class = ContextMenuLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = ContextMenuLayoutFilterSet

    @action(detail=True, methods=["get"], url_path="ping")
    def ping(self, request, pk=None, realm_code=None, space_code=None):
        layout = self.get_object()

        return Response(
            {
                "id": layout.id,
                "modified_at": layout.modified_at,
                "is_default": layout.is_default,
            }
        )


class ListLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    is_default = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    name = CharFilter()
    # user_code = CharFilter()
    user_code = CharExactFilter()
    content_type = LayoutContentTypeFilter()

    class Meta:
        model = ListLayout
        fields = ["content_type", "name"]


class ListLayoutViewSet(AbstractModelViewSet, DestroyModelMixinExt):
    queryset = ListLayout.objects.select_related("member", "content_type")
    serializer_class = ListLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = ListLayoutFilterSet
    ordering_fields = ["content_type", "name", "is_default"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        url_path="light",
        serializer_class=ListLayoutLightSerializer,
    )
    def list_light(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginator.post_paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=["get"], url_path="ping")
    def ping(self, request, pk=None, realm_code=None, space_code=None):
        layout = self.get_object()

        try:
            return Response(
                {
                    "id": layout.id,
                    "modified_at": layout.modified_at,
                    "is_default": layout.is_default,
                }
            )
        except Exception as e:
            _l.error(e)
            _l.error(traceback.format_exc())


# DEPRECATED
class ListLayoutLightViewSet(AbstractModelViewSet):
    queryset = ListLayout.objects.select_related("member", "content_type")
    serializer_class = ListLayoutLightSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = ListLayoutFilterSet
    ordering_fields = ["content_type", "name", "is_default"]


class DashboardLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    is_default = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    name = CharFilter()

    class Meta:
        model = DashboardLayout
        fields = []


class DashboardLayoutViewSet(AbstractModelViewSet):
    queryset = DashboardLayout.objects.select_related("member")
    serializer_class = DashboardLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = DashboardLayoutFilterSet
    ordering_fields = ["name", "is_default"]

    @action(detail=True, methods=["get"], url_path="ping")
    def ping(self, request, pk=None, realm_code=None, space_code=None):
        layout = self.get_object()

        return Response(
            {
                "id": layout.id,
                "modified_at": layout.modified_at,
                "is_default": layout.is_default,
            }
        )


class DashboardLayoutLightViewSet(AbstractModelViewSet):
    queryset = DashboardLayout.objects.select_related("member")
    serializer_class = DashboardLayoutLightSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = DashboardLayoutFilterSet
    ordering_fields = ["name", "is_default"]


class MobileLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    is_default = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    name = CharFilter()

    class Meta:
        model = MobileLayout
        fields = []


class MobileLayoutViewSet(AbstractModelViewSet):
    queryset = MobileLayout.objects.select_related("member")
    serializer_class = MobileLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = MobileLayoutFilterSet
    ordering_fields = ["name", "is_default"]

    @action(detail=True, methods=["get"], url_path="ping")
    def ping(self, request, pk=None, realm_code=None, space_code=None):
        layout = self.get_object()

        return Response(
            {
                "id": layout.id,
                "modified_at": layout.modified_at,
                "is_default": layout.is_default,
            }
        )


class MemberLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    is_default = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    name = CharFilter()

    class Meta:
        model = MemberLayout
        fields = []


class MemberLayoutViewSet(AbstractModelViewSet):
    queryset = MemberLayout.objects.select_related("member")
    serializer_class = MemberLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = MemberLayoutFilterSet
    ordering_fields = ["name", "is_default"]

    @action(detail=True, methods=["get"], url_path="ping")
    def ping(self, request, pk=None, realm_code=None, space_code=None):
        layout = self.get_object()

        return Response(
            {
                "id": layout.id,
                "modified_at": layout.modified_at,
                "is_default": layout.is_default,
            }
        )


class ConfigurationExportLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    is_default = django_filters.BooleanFilter()
    name = CharFilter()

    class Meta:
        model = ConfigurationExportLayout
        fields = []


class ConfigurationExportLayoutViewSet(AbstractModelViewSet):
    queryset = ConfigurationExportLayout.objects.select_related("member")
    serializer_class = ConfigurationExportLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = ConfigurationExportLayoutFilterSet
    ordering_fields = ["name", "is_default"]

    @action(detail=True, methods=["get"], url_path="ping")
    def ping(self, request, pk=None, realm_code=None, space_code=None):
        layout = self.get_object()

        return Response(
            {
                "id": layout.id,
                "modified_at": layout.modified_at,
                "is_default": layout.is_default,
            }
        )


class EditLayoutFilterSet(FilterSet):
    id = NoOpFilter()
    content_type = LayoutContentTypeFilter()
    is_default = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    name = CharFilter()
    user_code = CharFilter()

    class Meta:
        model = EditLayout
        fields = []


class EditLayoutViewSet(AbstractModelViewSet):
    queryset = EditLayout.objects.select_related("member", "content_type")
    serializer_class = EditLayoutSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = EditLayoutFilterSet
    ordering_fields = [
        "content_type",
    ]

    @action(detail=True, methods=["get"], url_path="ping")
    def ping(self, request, pk=None, realm_code=None, space_code=None):
        layout = self.get_object()

        return Response(
            {
                "id": layout.id,
                "modified_at": layout.modified_at,
                "is_default": layout.is_default,
            }
        )


class BookmarkFilterSet(FilterSet):
    id = NoOpFilter()

    class Meta:
        model = Bookmark
        fields = []


class BookmarkViewSet(AbstractModelViewSet):
    queryset = Bookmark.objects.prefetch_related(
        "member",
        "list_layout",
        "list_layout__content_type",
        "parent",
        "children",
    ).filter(parent__isnull=True)
    serializer_class = BookmarkSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = BookmarkFilterSet
    ordering_fields = [
        "name",
        "position",
    ]


class SystemAttributesViewSet(AbstractViewSet):
    @staticmethod
    def list(request, *args, **kwargs):
        props = {
            "portfolios.portfolio": Portfolio.get_system_attrs(),
            "accounts.account": Account.get_system_attrs(),
            "accounts.accounttype": AccountType.get_system_attrs(),
            "instruments.instrument": Instrument.get_system_attrs(),
            "instruments.instrumenttype": InstrumentType.get_system_attrs(),
            "currencies.currency": Currency.get_system_attrs(),
            "counterparties.counterparty": Counterparty.get_system_attrs(),
            "counterparties.counterpartygroup": CounterpartyGroup.get_system_attrs(),
            "counterparties.responsible": Responsible.get_system_attrs(),
            "counterparties.responsiblegroup": ResponsibleGroup.get_system_attrs(),
            "transactions.transactiontype": TransactionType.get_system_attrs(),
            "transactions.transactiontypegroup": TransactionTypeGroup.get_system_attrs(),
            "strategies.strategy1": Strategy1.get_system_attrs(),
            "strategies.strategy1subgroup": Strategy1Subgroup.get_system_attrs(),
            "strategies.strategy2": Strategy2.get_system_attrs(),
            "strategies.strategy2subgroup": Strategy2Subgroup.get_system_attrs(),
            "strategies.strategy3": Strategy3.get_system_attrs(),
            "strategies.strategy3subgroup": Strategy3Subgroup.get_system_attrs(),
            "reports.balancereport": BalanceReport.get_system_attrs(),
            "reports.transactionreport": TransactionReport.get_system_attrs(),
        }

        return Response(props)


class DraftFilterSet(FilterSet):
    id = NoOpFilter()
    name = CharFilter()
    user_code = CharFilter()

    class Meta:
        model = Draft
        fields = []


class DraftViewSet(AbstractModelViewSet):
    queryset = Draft.objects.select_related("member")
    serializer_class = DraftSerializer
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMemberFilter,
    ]
    filter_class = DraftFilterSet
    ordering_fields = ["name", "is_default"]
