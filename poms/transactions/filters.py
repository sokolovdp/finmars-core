from django.db.models import Q
from rest_framework.filters import BaseFilterBackend

from poms.accounts.models import Account
from poms.obj_perms.utils import obj_perms_filter_objects_for_view
from poms.portfolios.models import Portfolio


class TransactionObjectPermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        member = request.user.member
        master_user = request.user.master_user
        if member.is_superuser:
            return queryset
        portfolio_qs = obj_perms_filter_objects_for_view(member, Portfolio.objects.filter(master_user=master_user))
        account_position_qs = obj_perms_filter_objects_for_view(member, Account.objects.filter(master_user=master_user))
        account_cash_qs = obj_perms_filter_objects_for_view(member, Account.objects.filter(master_user=master_user))
        account_interim_qs = obj_perms_filter_objects_for_view(member, Account.objects.filter(master_user=master_user))
        # portfolio_qs = ObjectPermissionFilter().filter_queryset(
        #     request, Portfolio.objects.filter(master_user=master_user), view)
        # account_position_qs = ObjectPermissionFilter().filter_queryset(
        #     request, Account.objects.filter(master_user=master_user), view)
        # account_cash_qs = ObjectPermissionFilter().filter_queryset(
        #     request, Account.objects.filter(master_user=master_user), view)
        # account_interim_qs = ObjectPermissionFilter().filter_queryset(
        #     request, Account.objects.filter(master_user=master_user), view)
        queryset = queryset.filter(
            Q(portfolio__in=portfolio_qs) & (
                Q(account_position__in=account_position_qs) |
                Q(account_cash__in=account_cash_qs) |
                Q(account_interim__in=account_interim_qs)
            )
        )
        return queryset
