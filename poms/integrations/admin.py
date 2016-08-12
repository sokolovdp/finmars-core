from __future__ import unicode_literals, print_function

from django import forms
from django.conf import settings
from django.contrib import admin
from kombu.transport.django.models import Queue, Message

from poms.audit.admin import HistoricalAdmin
from poms.common.admin import ClassModelAdmin
from poms.integrations.models import InstrumentMapping, InstrumentMappingAttribute, BloombergTask, BloombergConfig, \
    InstrumentMappingInput, ProviderClass, FactorScheduleMethod, AccrualCalculationScheduleMethod, PricingFieldMapping, \
    CurrencyMapping, InstrumentTypeMapping, InstrumentAttributeValueMapping

if settings.DEBUG and 'kombu.transport.django' in settings.INSTALLED_APPS:
    class QueueAdmin(admin.ModelAdmin):
        model = Queue
        list_display = ('id', 'name')
        list_display_links = ('id',)
        search_fields = ('name',)


    admin.site.register(Queue, QueueAdmin)


    class MessageAdmin(admin.ModelAdmin):
        model = Message
        list_display = ('id', '_queue', 'visible', 'sent_at',)
        list_display_links = ('id',)
        # list_filter = ('queue',)
        search_fields = ('queue__name',)
        date_hierarchy = 'sent_at'
        raw_id_fields = ('queue',)
        list_select_related = ('queue',)

        def _queue(self, instanse):
            return instanse.queue.name

        _queue.short_description = 'Queue'
        _queue.admin_order_field = 'queue__name'


    admin.site.register(Message, MessageAdmin)


class InstrumentMappingInputInline(admin.TabularInline):
    model = InstrumentMappingInput
    extra = 0


class InstrumentMappingAttributeInline(admin.TabularInline):
    model = InstrumentMappingAttribute
    extra = 0
    raw_id_fields = ['attribute_type']


class InstrumentMappingAdmin(HistoricalAdmin):
    model = InstrumentMapping
    inlines = [
        InstrumentMappingInputInline,
        InstrumentMappingAttributeInline,
    ]
    list_display = ['id', 'master_user', 'mapping_name']
    list_select_related = ['master_user', ]
    raw_id_fields = ['master_user', ]
    search_fields = ['mapping_name', ]


admin.site.register(InstrumentMapping, InstrumentMappingAdmin)


class BloombergConfigForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = BloombergConfig
        fields = ['master_user', 'p12cert', 'password', 'cert', 'key']


class BloombergConfigAdmin(HistoricalAdmin):
    model = BloombergConfig
    form = BloombergConfigForm
    list_display = ['id', 'master_user', ]
    list_select_related = ['master_user', ]
    raw_id_fields = ['master_user', ]


admin.site.register(BloombergConfig, BloombergConfigAdmin)


class BloombergTaskAdmin(admin.ModelAdmin):
    model = BloombergTask
    list_display = ['id', 'created', 'master_user', 'member', 'action', 'status', ]
    list_select_related = ['master_user', 'member', ]
    raw_id_fields = ['master_user', 'member', ]
    search_fields = ['action', 'response_id', ]
    list_filter = ['created', 'action', 'status', ]
    date_hierarchy = 'created'

    # if not settings.DEBUG:
    # def has_add_permission(self, request):
    #     return settings.DEBUG

    def save_model(self, request, obj, form, change):
        pass


admin.site.register(BloombergTask, BloombergTaskAdmin)

admin.site.register(ProviderClass, ClassModelAdmin)
admin.site.register(FactorScheduleMethod, ClassModelAdmin)
admin.site.register(AccrualCalculationScheduleMethod, ClassModelAdmin)


class PricingFieldMappingAdmin(admin.ModelAdmin):
    model = PricingFieldMapping
    list_display = ['id', 'master_user', 'provider']
    list_select_related = ['master_user', 'provider']
    raw_id_fields = ['master_user']


admin.site.register(PricingFieldMapping, PricingFieldMappingAdmin)


class CurrencyMappingAdmin(admin.ModelAdmin):
    model = CurrencyMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'currency']
    list_select_related = ['currency__master_user', 'currency', 'provider']
    raw_id_fields = ['currency']

    def master_user(self, obj):
        return obj.currency.master_user


admin.site.register(CurrencyMapping, CurrencyMappingAdmin)


class InstrumentTypeMappingAdmin(admin.ModelAdmin):
    model = InstrumentTypeMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'instrument_type']
    list_select_related = ['instrument_type__master_user', 'instrument_type', 'provider']
    raw_id_fields = ['instrument_type']

    def master_user(self, obj):
        return obj.instrument_type.master_user


admin.site.register(InstrumentTypeMapping, InstrumentTypeMappingAdmin)


class InstrumentAttributeValueMappingAdmin(admin.ModelAdmin):
    model = InstrumentAttributeValueMapping
    list_display = ['id', 'master_user', 'provider', 'value', 'attribute_type']
    list_select_related = ['attribute_type__master_user', 'attribute_type', 'classifier', 'provider']
    raw_id_fields = ['attribute_type', 'classifier']

    def master_user(self, obj):
        return obj.attribute_type.master_user

        # provider = models.ForeignKey(ProviderClass)
        # value = models.CharField(max_length=255)
        #
        # attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', on_delete=models.PROTECT,
        #                                    verbose_name=_('attribute type'))
        # value_string = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('value (String)'))
        # value_float = models.FloatField(null=True, blank=True, verbose_name=_('value (Float)'))
        # value_date = models.DateField(null=True, blank=True, verbose_name=_('value (Date)'))
        # classifier = models.ForeignKey('instruments.InstrumentClassifier', on_delete=models.PROTECT, null=True, blank=True,
        #                                verbose_name=_('classifier'))


admin.site.register(InstrumentAttributeValueMapping, InstrumentAttributeValueMappingAdmin)
