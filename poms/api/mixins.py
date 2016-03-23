from __future__ import unicode_literals

from django.db import transaction
from rest_framework import permissions
from reversion import revisions as reversion

from poms.audit.models import VersionInfo


class DbTransactionMixin(object):
    def __init__(self, *args, **kwargs):
        self.reversion_is_active = False

    def dispatch(self, request, *args, **kwargs):
        self.reversion_is_active = False
        method = request.method.upper()
        if method in permissions.SAFE_METHODS:
            return super(DbTransactionMixin, self).dispatch(request, *args, **kwargs)
        else:
            with transaction.atomic(), reversion.create_revision():
                self.reversion_is_active = True
                # reversion.set_comment("Comment text...")
                return super(DbTransactionMixin, self).dispatch(request, *args, **kwargs)

    def initial(self, request, *args, **kwargs):
        super(DbTransactionMixin, self).initial(request, *args, **kwargs)
        if self.reversion_is_active:
            reversion.set_user(request.user)

            profile = getattr(request.user, 'profile', None)
            master_user = getattr(profile, 'master_user', None)
            if master_user:
                reversion.add_meta(VersionInfo, master_user=master_user, username=request.user.username)

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
