from __future__ import unicode_literals

from django.db import transaction
from rest_framework import permissions


class DbTransactionMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.method.upper() in permissions.SAFE_METHODS:
            return super(DbTransactionMixin, self).dispatch(request, *args, **kwargs)
        else:
            with transaction.atomic():
                return super(DbTransactionMixin, self).dispatch(request, *args, **kwargs)
