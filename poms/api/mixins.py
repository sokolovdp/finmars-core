from __future__ import unicode_literals

from django.db import transaction
from rest_framework import permissions


class TransactionMixin(object):
    def dispatch(self, request, *args, **kwargs):
        method = request.method.upper()
        if method in permissions.SAFE_METHODS:
            return super(TransactionMixin, self).dispatch(request, *args, **kwargs)
        else:
            with transaction.atomic():
                return super(TransactionMixin, self).dispatch(request, *args, **kwargs)


# def initial(self, request, *args, **kwargs):
#     super(LagoonMixin, self).initial(request, *args, **kwargs)
#     if not is_session_authenticator(request):
#         AccountMiddleware.process_request(request)
#     # self._post_init(request)
#
# # def _post_init(self, request):
# #     if not is_session_authenticator(request):
# #         self._old = personalization.activate(request)
#
# # def _post_dispatch(self, request):
# #     if hasattr(self, '_old') and self._old:
# #         personalization.deactivate(*self._old)
