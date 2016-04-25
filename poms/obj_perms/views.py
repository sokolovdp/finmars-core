from rest_framework.decorators import detail_route
from rest_framework.viewsets import ModelViewSet


class ModelWithObjectPermissionViewSet(ModelViewSet):

    def get_queryset(self):
        qs = super(ModelWithObjectPermissionViewSet, self).get_queryset()
        return qs.prefetch_related('user_object_permissions', 'group_object_permissions')
