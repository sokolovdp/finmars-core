from rest_framework.filters import BaseFilterBackend

from poms.instruments.models import InstrumentAttributeType, InstrumentType
from poms.obj_perms.utils import obj_perms_filter_objects_for_view


class TaskFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        # master_user = get_master_user(request)
        master_user = request.user.master_user
        member = request.user.member
        if member.is_superuser:
            return queryset.filter(master_user=master_user)
        else:
            return queryset.filter(master_user=master_user, member=member)


class InstrumentTypeMappingObjectPermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        member = request.user.member
        master_user = request.user.master_user
        if member.is_superuser:
            return queryset
        instr_types_qs = obj_perms_filter_objects_for_view(member,
                                                           InstrumentType.objects.filter(master_user=master_user))
        queryset = queryset.filter(instrument_type__in=instr_types_qs)
        return queryset


class InstrumentAttributeValueMappingObjectPermissionFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        member = request.user.member
        master_user = request.user.master_user
        if member.is_superuser:
            return queryset
        attr_types_qs = obj_perms_filter_objects_for_view(member, InstrumentAttributeType.objects.filter(
            master_user=master_user))
        queryset = queryset.filter(attribute_type__in=attr_types_qs)
        return queryset
