from __future__ import unicode_literals


# class DbTransactionMixin(object):
#     def dispatch(self, request, *args, **kwargs):
#         if request.method.upper() in permissions.SAFE_METHODS:
#             return super(DbTransactionMixin, self).dispatch(request, *args, **kwargs)
#         else:
#             with transaction.atomic():
#                 return super(DbTransactionMixin, self).dispatch(request, *args, **kwargs)
