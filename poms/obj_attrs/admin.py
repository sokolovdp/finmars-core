from django.contrib import admin
from django.contrib.admin import widgets
from django.db import models

from poms.audit.admin import HistoricalAdmin
from poms.common.models import NamedModel
from poms.obj_attrs.models import AbstractAttributeTypeOption, AbstractAttribute, AbstractClassifier


class AbstractAttributeTypeAdmin(HistoricalAdmin):
    list_display = ['id', 'master_user', 'name', 'value_type', ]
    list_select_related = ['master_user', ]
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


class AbstractAttributeTypeOptionAdmin(HistoricalAdmin):
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
