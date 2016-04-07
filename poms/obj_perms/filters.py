#
# class PomsObjectPermissionsFilter(BaseFilterBackend):
#     # perm_format = '%(app_label)s.view_%(model_name)s'
#     perm_format = '%(app_label)s.change_%(model_name)s'
#
#     def filter_queryset(self, request, queryset, view):
#         user = request.user
#         model_cls = queryset.model
#         kwargs = {
#             'app_label': model_cls._meta.app_label,
#             'model_name': model_cls._meta.model_name
#         }
#         perm = self.perm_format % kwargs
#         return filter_objects_for_user(user, [perm], queryset)

