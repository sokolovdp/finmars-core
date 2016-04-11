from django.contrib import admin

from poms.audit.admin import HistoricalAdmin
from poms.obj_attrs.models import AttributeType, Attribute, AttributeTypeOrder


# class AttrInlineBase(admin.StackedInline):
#     ordering = ['order', 'name']
#     raw_id_fields = ['classifier']
#     extra = 0
#
#
# class AttrValueInlineBase(admin.StackedInline):
#     extra = 0
#     raw_id_fields = ['attr', 'classifier']
#
#
# class AccountAttrInline(AttrInlineBase):
#     model = AccountAttr
#
#
# class CounterpartyAttrInline(AttrInlineBase):
#     model = CounterpartyAttr
#
#
# class ResponsibleAttrInline(AttrInlineBase):
#     model = ResponsibleAttr
#
#
# class PortfolioAttrInline(AttrInlineBase):
#     model = PortfolioAttr
#
#
# class InstrumentAttrInline(AttrInlineBase):
#     model = InstrumentAttr
#
#
# class TransactionAttrInline(AttrInlineBase):
#     model = TransactionAttr
#     raw_id_fields = ['strategy_position', 'strategy_cash']
#     ordering = ['order', 'name']
#     extra = 0
#
#
# class AttrAdmin(HistoricalAdmin):
#     list_display = ['id', 'master_user', 'name', 'value_type', 'classifier']
#     list_select_related = ['master_user', 'classifier']
#     raw_id_fields = ['master_user', 'classifier']
#
#
# class AttrValueAdmin(HistoricalAdmin):
#     list_display = ['id', 'content_object', 'attr', 'value', 'classifier']
#     list_select_related = ['attr', 'attr__master_user', 'classifier']
#     raw_id_fields = ['attr', 'content_object', 'classifier']
#
#
# class TransactionAttrAdmin(AttrAdmin):
#     list_display = ['id', 'master_user', 'name', 'value_type', 'strategy_position', 'strategy_cash']
#     list_select_related = ['master_user', 'strategy_position', 'strategy_cash']
#     raw_id_fields = ['master_user', 'strategy_position', 'strategy_cash']
#
#
# class TransactionAttrValueAdmin(AttrValueAdmin):
#     list_display = ['id', 'content_object', 'attr', 'value', 'strategy_position', 'strategy_cash']
#     list_select_related = ['attr', 'attr__master_user', 'strategy_position', 'strategy_cash']
#     raw_id_fields = ['attr', 'content_object', 'strategy_position', 'strategy_cash']
#
#
# admin.site.register(AccountAttr, AttrAdmin)
# admin.site.register(AccountAttrValue, AttrValueAdmin)
# admin.site.register(CounterpartyAttr, AttrAdmin)
# admin.site.register(CounterpartyAttrValue, AttrValueAdmin)
# admin.site.register(ResponsibleAttr, AttrAdmin)
# admin.site.register(ResponsibleAttrValue, AttrValueAdmin)
# admin.site.register(InstrumentAttr, AttrAdmin)
# admin.site.register(InstrumentAttrValue, AttrValueAdmin)
# admin.site.register(PortfolioAttr, AttrAdmin)
# admin.site.register(PortfolioAttrValue, AttrValueAdmin)
# admin.site.register(TransactionAttr, TransactionAttrAdmin)
# admin.site.register(TransactionAttrValue, TransactionAttrValueAdmin)


# class AttributeChoiceInline(admin.TabularInline):
#     model = AttributeChoice
#     extra = 0


class AttributeTypeAdmin(HistoricalAdmin):
    model = AttributeType
    list_display = ['id', 'master_user', 'content_type', 'name', 'value_type']
    fields = ('master_user', 'content_type', 'name', 'value_type', 'order',
              ('classifier_content_type', 'classifier_object_id',), 'classifier')
    readonly_fields = ('classifier',)
    raw_id_fields = ['master_user']

    # inlines = [AttributeChoiceInline]

    def get_readonly_fields(self, request, obj=None):
        ro = super(AttributeTypeAdmin, self).get_readonly_fields(request, obj=obj)
        if obj:
            ro += ('master_user', 'content_type', 'value_type', 'classifier_content_type')
            t = obj.value_type
            if t == AttributeType.NUMBER or t == AttributeType.STRING:
                ro += ('classifier_object_id',)
            elif t == AttributeType.CLASSIFIER:
                pass
                # elif t == Attribute.CHOICE or t == Attribute.CHOICES:
                #     ro += ('classifier_object_id',)
        return ro

    def get_inline_instances(self, request, obj=None):
        # if obj and (obj.value_type == Attribute.CHOICE or obj.value_type == Attribute.CHOICES):
        #     return super(AttributeAdmin, self).get_inline_instances(request, obj)
        return []


class AttributeAdmin(HistoricalAdmin):
    model = Attribute
    # filter_horizontal = ['choices']
    list_display = ['id', 'master_user', 'attribute_type', 'content_object', '__str__']
    # 'choices',
    fields = ('attribute_type', ('content_type', 'object_id',), 'value',
              ('classifier_content_type', 'classifier_object_id',), 'classifier')
    readonly_fields = ('classifier',)
    raw_id_fields = ['attribute_type']

    def master_user(self, obj):
        return obj.attribute_type.master_user

    master_user.admin_order_field = 'attribute__master_user'

    def get_readonly_fields(self, request, obj=None):
        ro = super(AttributeAdmin, self).get_readonly_fields(request, obj=obj)
        if obj:
            ro += ('attribute', 'content_type')
            t = obj.attribute_type.value_type
            if t == AttributeType.NUMBER or t == AttributeType.STRING:
                ro += ('choices', 'classifier_content_type', 'classifier_object_id')
            elif t == AttributeType.CLASSIFIER:
                ro += ('value', 'choices', 'classifier_content_type')
            # elif t == Attribute.CHOICE or t == Attribute.CHOICES:
            #     ro += ('value', 'classifier_content_type', 'classifier_object_id')
            return ro
        else:
            return ro + ('choices',)

    def get_object(self, request, object_id, from_field=None):
        self._object = super(AttributeAdmin, self).get_object(request, object_id, from_field=from_field)
        # print('get_object: ', self._object)
        return self._object

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'choices':
            obj = getattr(self, '_object', None)
            print('formfield_for_manytomany: ', obj)
            qs = kwargs.get('queryset', db_field.remote_field.model.objects)
            if obj is None:
                kwargs['queryset'] = qs.none()
            else:
                kwargs['queryset'] = qs.filter(attribute_type=obj.attribute_type)
        return super(AttributeAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)


class AttributeTypeOrderAdmin(HistoricalAdmin):
    model = AttributeTypeOrder
    list_display = ['id', 'member', 'attribute_type', 'order', 'is_hidden']
    raw_id_fields = ['member', 'attribute_type']


admin.site.register(AttributeType, AttributeTypeAdmin)
admin.site.register(AttributeTypeOrder, AttributeTypeOrderAdmin)
admin.site.register(Attribute, AttributeAdmin)
# admin.site.register(Classifier, TreeModelAdmin)
# register_admin(Attribute)
