from django.contrib import admin

from poms.audit.admin import HistoricalAdmin


# class AttributeTypeAdmin(HistoricalAdmin):
#     model = AttributeType
#     list_display = ['id', 'master_user', 'content_type', 'name', 'value_type']
#     fields = ('master_user', 'content_type', 'name', 'value_type', 'order',
#               ('classifier_content_type', 'classifier_object_id',), 'classifier')
#     readonly_fields = ('classifier',)
#     raw_id_fields = ['master_user']
#
#     # inlines = [AttributeChoiceInline]
#
#     def get_readonly_fields(self, request, obj=None):
#         ro = super(AttributeTypeAdmin, self).get_readonly_fields(request, obj=obj)
#         if obj:
#             ro += ('master_user', 'content_type', 'value_type', 'classifier_content_type')
#             t = obj.value_type
#             if t == AttributeType.NUMBER or t == AttributeType.STRING:
#                 ro += ('classifier_object_id',)
#             elif t == AttributeType.CLASSIFIER:
#                 pass
#                 # elif t == Attribute.CHOICE or t == Attribute.CHOICES:
#                 #     ro += ('classifier_object_id',)
#         return ro
#
#     def get_inline_instances(self, request, obj=None):
#         # if obj and (obj.value_type == Attribute.CHOICE or obj.value_type == Attribute.CHOICES):
#         #     return super(AttributeAdmin, self).get_inline_instances(request, obj)
#         return []
#
#
# class AttributeAdmin(HistoricalAdmin):
#     model = Attribute
#     # filter_horizontal = ['choices']
#     list_display = ['id', 'master_user', 'attribute_type', 'content_object', '__str__']
#     # 'choices',
#     fields = ('attribute_type', ('content_type', 'object_id',), 'value',
#               ('classifier_content_type', 'classifier_object_id',), 'classifier')
#     readonly_fields = ('classifier',)
#     raw_id_fields = ['attribute_type']
#
#     def master_user(self, obj):
#         return obj.attribute_type.master_user
#
#     master_user.admin_order_field = 'attribute__master_user'
#
#     def get_readonly_fields(self, request, obj=None):
#         ro = super(AttributeAdmin, self).get_readonly_fields(request, obj=obj)
#         if obj:
#             ro += ('attribute', 'content_type')
#             t = obj.attribute_type.value_type
#             if t == AttributeType.NUMBER or t == AttributeType.STRING:
#                 ro += ('choices', 'classifier_content_type', 'classifier_object_id')
#             elif t == AttributeType.CLASSIFIER:
#                 ro += ('value', 'choices', 'classifier_content_type')
#             # elif t == Attribute.CHOICE or t == Attribute.CHOICES:
#             #     ro += ('value', 'classifier_content_type', 'classifier_object_id')
#             return ro
#         else:
#             return ro + ('choices',)
#
#     def get_object(self, request, object_id, from_field=None):
#         self._object = super(AttributeAdmin, self).get_object(request, object_id, from_field=from_field)
#         # print('get_object: ', self._object)
#         return self._object
#
#     def formfield_for_manytomany(self, db_field, request=None, **kwargs):
#         if db_field.name == 'choices':
#             obj = getattr(self, '_object', None)
#             print('formfield_for_manytomany: ', obj)
#             qs = kwargs.get('queryset', db_field.remote_field.model.objects)
#             if obj is None:
#                 kwargs['queryset'] = qs.none()
#             else:
#                 kwargs['queryset'] = qs.filter(attribute_type=obj.attribute_type)
#         return super(AttributeAdmin, self).formfield_for_manytomany(db_field, request=request, **kwargs)
#
#
# class AttributeTypeOrderAdmin(HistoricalAdmin):
#     model = AttributeTypeOrder
#     list_display = ['id', 'member', 'attribute_type', 'order', 'is_hidden']
#     raw_id_fields = ['member', 'attribute_type']
#
#
# admin.site.register(AttributeType, AttributeTypeAdmin)
# admin.site.register(AttributeTypeOrder, AttributeTypeOrderAdmin)
# admin.site.register(Attribute, AttributeAdmin)


class AttributeTypeAdminBase(HistoricalAdmin):
    list_display = ['id', 'master_user', 'name', 'value_type', 'classifier_root', ]
    list_select_related = ['master_user', 'classifier_root', ]
    raw_id_fields = ['master_user', 'classifier_root']
    save_as = True


class AttributeTypeOptionInlineBase(HistoricalAdmin):
    extra = 0
    list_display = ['id', 'member', 'attribute_type', 'is_hidden']
    fields = ['member', 'attribute_type', 'is_hidden']
    raw_id_fields = ['member']


class AttributeInlineBase(admin.TabularInline):
    extra = 0
    fields = ['attribute_type', 'value_string', 'value_float', 'value_date', 'classifier']
    raw_id_fields = ['attribute_type', 'classifier']
