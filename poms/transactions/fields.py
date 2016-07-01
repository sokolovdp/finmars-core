from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from rest_framework.fields import CharField, empty

from poms.common.fields import FilteredPrimaryKeyRelatedField, FilteredSlugRelatedField
from poms.obj_perms.fields import PrimaryKeyRelatedFilteredWithObjectPermissionField
from poms.obj_perms.filters import ObjectPermissionBackend
from poms.transactions.filters import TransactionTypeInputContentTypeFilter
from poms.transactions.models import TransactionType, TransactionAttributeType, TransactionTypeGroup
from poms.users.filters import OwnerByMasterUserFilter


# class TransactionTypeGroupField(FilteredPrimaryKeyRelatedField):
#     queryset = TransactionTypeGroup.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class TransactionTypeGroupField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = TransactionTypeGroup.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


# class TransactionTypeField(FilteredPrimaryKeyRelatedField):
#     queryset = TransactionType.objects
#     filter_backends = [
#         OwnerByMasterUserFilter,
#         FieldObjectPermissionBackend,
#     ]
class TransactionTypeField(PrimaryKeyRelatedFilteredWithObjectPermissionField):
    queryset = TransactionType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
    ]


class TransactionAttributeTypeField(FilteredPrimaryKeyRelatedField):
    queryset = TransactionAttributeType.objects
    filter_backends = [
        OwnerByMasterUserFilter,
        ObjectPermissionBackend,
    ]


class TransactionTypeInputContentTypeField(FilteredSlugRelatedField):
    queryset = ContentType.objects
    filter_backends = [
        TransactionTypeInputContentTypeFilter
    ]

    def __init__(self, **kwargs):
        kwargs['slug_field'] = 'model'
        super(TransactionTypeInputContentTypeField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            app_label, model = data.split('.')
            return self.get_queryset().get(app_label=app_label, model=model)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', slug_name=self.slug_field, value=smart_text(data))
        except (TypeError, ValueError):
            self.fail('invalid')

    def to_representation(self, obj):
        return '%s.%s' % (obj.app_label, obj.model)


class ExpressionField(CharField):
    def __init__(self, **kwargs):
        kwargs['allow_null'] = kwargs.get('allow_null', False)
        kwargs['allow_blank'] = kwargs.get('allow_blank', False)
        super(ExpressionField, self).__init__(**kwargs)

    def run_validation(self, data=empty):
        value = super(ExpressionField, self).run_validation(data)
        if data:
            from poms.common import formula
            formula.validate(data)
            # try:
            #     formula.try_parse(data)
            # except formula.InvalidExpression as e:
            #     raise ValidationError('Invalid expression: %s' % e)
        return value
