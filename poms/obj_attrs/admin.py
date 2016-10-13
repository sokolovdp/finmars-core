from django.contrib import admin

from poms.obj_attrs.models import AbstractAttributeTypeOption, AbstractAttribute, AbstractClassifier, \
    GenericAttributeType, GenericClassifier, GenericAttribute, GenericAttributeTypeOption


class AbstractAttributeTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'master_user', 'user_code', 'name', 'value_type', ]
    list_select_related = ['master_user', ]
    ordering = ['master_user', 'user_code']
    list_filter = ['value_type']
    search_fields = ['id', 'name']
    raw_id_fields = ['master_user']
    save_as = True


class AbstractAttributeTypeClassifierInline(admin.TabularInline):
    extra = 0
    fields = ['id', 'name', 'parent']
    raw_id_fields = ['parent']
    readonly_fields = ['id']
    # formfield_overrides = {
    #     models.TextField: {'widget': widgets.AdminTextInputWidget},
    # }
    model = AbstractClassifier

    def __init__(self, parent_model, *args, **kwargs):
        # _, self.model = get_rel_model(parent_model, 'attribute_type', MPTTModel)
        self.model = parent_model._meta.get_field('classifiers').related_model
        super(AbstractAttributeTypeClassifierInline, self).__init__(parent_model, *args, **kwargs)


class AbstractAttributeTypeOptionInline(admin.TabularInline):
    extra = 0
    fields = ['member', 'is_hidden', ]
    raw_id_fields = ['member']
    model = AbstractAttributeTypeOption

    def __init__(self, parent_model, *args, **kwargs):
        self.model = parent_model._meta.get_field('options').related_model
        super(AbstractAttributeTypeOptionInline, self).__init__(parent_model, *args, **kwargs)


class AbstractAttributeTypeOptionAdmin(admin.ModelAdmin):
    extra = 0
    list_display = ['id', 'member', 'attribute_type', 'is_hidden']
    fields = ['member', 'attribute_type', 'is_hidden']
    raw_id_fields = ['member']


class AbstractAttributeInline(admin.TabularInline):
    extra = 0
    fields = ['attribute_type', 'value_string', 'value_float', 'value_date', 'classifier']
    raw_id_fields = ['attribute_type', 'classifier']
    model = AbstractAttribute

    def __init__(self, parent_model, *args, **kwargs):
        self.model = parent_model._meta.get_field('attributes').related_model
        super(AbstractAttributeInline, self).__init__(parent_model, *args, **kwargs)



class GenericAttributeTypeOptionInline(admin.TabularInline):
    model = GenericAttributeTypeOption
    extra = 0
    raw_id_fields = ['member']


class GenericAttributeTypeAdmin(admin.ModelAdmin):
    model = GenericAttributeType
    list_display = ['id', 'master_user', 'content_type', 'value_type']
    list_select_related = ['content_type', 'content_type']
    list_filter = ['value_type']
    search_fields = ['user_code']
    raw_id_fields = ['master_user']
    inlines = [GenericAttributeTypeOptionInline]
    save_as = True


admin.site.register(GenericAttributeType, GenericAttributeTypeAdmin)


class GenericClassifierAdmin(admin.ModelAdmin):
    model = GenericClassifier
    list_display = ['id', 'master_user', 'attribute_type', 'tree_id', 'level', 'parent', 'name', ]
    list_select_related = ['attribute_type', 'attribute_type__master_user', 'parent']
    search_fields = ['name']
    raw_id_fields = ['attribute_type', 'parent']
    ordering = ['attribute_type', 'tree_id', 'level', ]
    save_as = True

    def master_user(self, obj):
        return obj.attribute_type.master_user

    master_user.admin_order_field = 'attribute_type__master_user'


admin.site.register(GenericClassifier, GenericClassifierAdmin)


class GenericAttributeAdmin(admin.ModelAdmin):
    model = GenericAttribute
    list_display = ['id', 'master_user', 'content_type', 'object_id', 'content_object', 'attribute_type',
                    'value_string', 'value_float', 'value_date', 'classifier', ]
    list_select_related = ['content_type', 'attribute_type', 'attribute_type__master_user', 'classifier']
    raw_id_fields = ['attribute_type', 'classifier']
    ordering = ['attribute_type__master_user', 'attribute_type', ]
    save_as = True

    def get_queryset(self, request):
        qs = super(GenericAttributeAdmin, self).get_queryset(request)
        return qs.prefetch_related('content_object')

    def master_user(self, obj):
        return obj.attribute_type.master_user

    master_user.admin_order_field = 'attribute_type__master_user'


admin.site.register(GenericAttribute, GenericAttributeAdmin)
