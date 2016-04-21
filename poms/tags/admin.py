from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from poms.accounts.models import AccountType, Account
from poms.audit.admin import HistoricalAdmin
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentType, Instrument
from poms.obj_perms.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy
from poms.tags.models import Tag, TagUserObjectPermission, TagGroupObjectPermission
from poms.transactions.models import TransactionType


class TagAdmin(HistoricalAdmin):
    model = Tag
    list_display = ['id', 'master_user', 'name']
    filter_horizontal = ['content_types', 'account_types', 'accounts', 'currencies', 'instrument_types', 'instruments',
                         'counterparties', 'responsibles', 'portfolios', 'transaction_types']

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_types':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            models = [AccountType, Account, Currency, InstrumentType, Instrument, Counterparty, Responsible, Strategy,
                      Portfolio, TransactionType]
            ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
            kwargs['queryset'] = qs.filter(pk__in=ctypes)
            # kwargs['queryset'] = qs.annotate(c=Concat('app_label', Value('.'), 'model')). \
            #     filter(c__in=[])
        return super(TagAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


admin.site.register(Tag, TagAdmin)

admin.site.register(TagUserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(TagGroupObjectPermission, GroupObjectPermissionAdmin)
