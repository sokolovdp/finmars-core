from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel

from poms.common.models import NamedModel
from poms.users.models import MasterUser


# @python_2_unicode_compatible
# class AttributeType(NamedModel):
#     STRING = 10
#     NUMBER = 20
#     CLASSIFIER = 30
#     # CHOICE = 40
#     # CHOICES = 50
#
#     VALUE_TYPES = (
#         (NUMBER, _('Number')),
#         (STRING, _('String')),
#         (CLASSIFIER, _('Classifier')),
#         # (CHOICE, _('Choice')),
#         # (CHOICES, _('Choices')),
#     )
#
#     master_user = models.ForeignKey(MasterUser, related_name='attribute_types')
#     content_type = models.ForeignKey(ContentType, related_name='attribute_types')
#     value_type = models.PositiveSmallIntegerField(choices=VALUE_TYPES, default=STRING)
#     order = models.IntegerField(default=0)
#
#     classifier_content_type = models.ForeignKey(ContentType, null=True, blank=True,
#                                                 related_name='attribute_type_classifiers')
#     classifier_object_id = models.BigIntegerField(null=True, blank=True)
#     classifier = GenericForeignKey(ct_field='classifier_content_type', fk_field='classifier_object_id')
#
#     class Meta:
#         unique_together = [
#             ['master_user', 'content_type', 'name']
#         ]
#         permissions = [
#             ('view_attribute_type', 'Can view attribute_type'),
#             ('share_attribute_type', 'Can share attribute_type'),
#             ('manage_attribute_type', 'Can manage attribute_type'),
#         ]
#
#     def __str__(self):
#         return self.name
#
#
# # register_model(AttributeType)
#
#
# @python_2_unicode_compatible
# class AttributeTypeOrder(models.Model):
#     member = models.ForeignKey('users.Member', related_name='attribute_orders')
#     attribute_type = models.ForeignKey(AttributeType, related_name='orders')
#     order = models.IntegerField(default=0)
#     is_hidden = models.BooleanField(default=False)
#
#     class Meta:
#         unique_together = [
#             ['member', 'attribute_type']
#         ]
#
#
# @python_2_unicode_compatible
# class Attribute(models.Model):
#     attribute_type = models.ForeignKey(AttributeType, related_name='attributes')
#
#     content_type = models.ForeignKey(ContentType, related_name='attributes')
#     object_id = models.BigIntegerField()
#     content_object = GenericForeignKey()
#
#     value = models.CharField(max_length=255, blank=True, default='')
#     # choices = models.ManyToManyField(AttributeChoice, blank=True)
#     # classifiers = TreeManyToManyField(Classifier, blank=True)
#
#     classifier_content_type = models.ForeignKey(ContentType, null=True, blank=True,
#                                                 related_name='attribute_classifiers')
#     classifier_object_id = models.BigIntegerField(null=True, blank=True)
#     classifier = GenericForeignKey(ct_field='classifier_content_type', fk_field='classifier_object_id')
#
#     def __str__(self):
#         # return '%s[%s] = %s' % (self.content_object, self.attribute, self._get_value())
#         return '%s' % self.get_display_value()
#
#     def get_display_value(self):
#         t = self.attribute_type.value_type
#         if t == AttributeType.NUMBER or t == AttributeType.STRING:
#             return self.value
#         elif t == AttributeType.CLASSIFIER:
#             return self.classifier
#         # elif t == Attribute.CHOICE or t == Attribute.CHOICES:
#         #     choices = [c.name for c in self.choices.all()]
#         #     return ', '.join(choices)
#         return None


class AttributeTypeBase(NamedModel):
    STRING = 10
    NUMBER = 20
    CLASSIFIER = 30
    # CHOICE = 40
    # CHOICES = 50

    VALUE_TYPES = (
        (NUMBER, _('Number')),
        (STRING, _('String')),
        (CLASSIFIER, _('Classifier')),
        # (CHOICE, _('Choice')),
        # (CHOICES, _('Choices')),
    )

    master_user = models.ForeignKey(MasterUser)
    value_type = models.PositiveSmallIntegerField(choices=VALUE_TYPES, default=STRING)
    order = models.IntegerField(default=0)

    class Meta:
        abstract = True
        unique_together = [
            ['master_user', 'name']
        ]


@python_2_unicode_compatible
class AttributeTypeOptionBase(models.Model):
    order = models.IntegerField(default=0)
    is_hidden = models.BooleanField(default=False)

    class Meta:
        abstract = True
        unique_together = [
            ['member', 'attribute_type']
        ]

    def __str__(self):
        return '%s - %s' % (self.member, self.attribute_type)


@python_2_unicode_compatible
class AttributeBase(models.Model):
    value = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '%s' % self.get_display_value()

    def get_display_value(self):
        t = self.attribute_type.value_type
        if t == AttributeTypeBase.NUMBER or t == AttributeTypeBase.STRING:
            return self.value
        elif t == AttributeTypeBase.CLASSIFIER:
            return self.classifier
        return None
