from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from poms.accounts.models import AccountType, Account
from poms.audit.admin import HistoricalAdmin
from poms.counterparties.models import Counterparty, Responsible
from poms.currencies.models import Currency
from poms.instruments.models import InstrumentType, Instrument
from poms.portfolios.models import Portfolio
from poms.strategies.models import Strategy1, Strategy2, Strategy3
from poms.transactions.models import TransactionType, Transaction
from poms.ui.models import TemplateListLayout, TemplateEditLayout, ListLayout, EditLayout


class BaseLayoutAdmin(HistoricalAdmin):
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'content_type':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            models = [
                AccountType,
                Account,
                Currency,
                InstrumentType,
                Instrument,
                Counterparty,
                Responsible,
                Portfolio,
                TransactionType,
                Transaction,
                Strategy1,
                Strategy2,
                Strategy3,
            ]
            ctypes = [ContentType.objects.get_for_model(model).pk for model in models]
            kwargs['queryset'] = qs.filter(pk__in=ctypes)
        return super(BaseLayoutAdmin, self).formfield_for_foreignkey(db_field, request=request, **kwargs)


class TemplateListLayoutAdmin(BaseLayoutAdmin):
    model = TemplateListLayout
    list_display = ['id', 'master_user', 'content_type', 'name']
    list_select_related = ['master_user', 'content_type']
    raw_id_fields = ['master_user']


admin.site.register(TemplateListLayout, TemplateListLayoutAdmin)


class TemplateEditLayoutAdmin(BaseLayoutAdmin):
    model = TemplateEditLayout
    list_display = ['id', 'master_user', 'content_type']
    list_select_related = ['master_user', 'content_type']
    raw_id_fields = ['master_user']


admin.site.register(TemplateEditLayout, TemplateEditLayoutAdmin)


class ListLayoutAdmin(BaseLayoutAdmin):
    model = ListLayout
    list_display = ['id', 'member', 'content_type', 'name']
    list_select_related = ['member', 'content_type']
    raw_id_fields = ['member']


admin.site.register(ListLayout, ListLayoutAdmin)


class EditLayoutAdmin(BaseLayoutAdmin):
    model = EditLayout
    list_display = ['id', 'member', 'content_type']
    list_select_related = ['member', 'content_type']
    raw_id_fields = ['member']


admin.site.register(EditLayout, EditLayoutAdmin)
