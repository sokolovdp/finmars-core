from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from poms.common.models import TimeStampedModel
from django.utils.translation import ugettext_lazy as _


MAPPING_FIELD_MAX_LENGTH = 32

@python_2_unicode_compatible
class InstrumentMapping(models.Model):
    master_user = models.ForeignKey('users.MasterUser')
    mapping_name = models.CharField(max_length=255)

    user_code = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    name = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH)
    short_name = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    public_name = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    notes = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)

    instrument_type = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    pricing_currency = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    price_multiplier = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    accrued_currency = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    accrued_multiplier = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    daily_pricing_model = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    payment_size_detail = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    default_price = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    default_accrued = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    user_text_1 = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    user_text_2 = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    user_text_3 = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    price_download_mode = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)

    class Meta:
        abstract = True
        index_together = (
            ('mapping', 'mapping_name')
        )
        verbose_name = _('instrument mapping')
        verbose_name_plural = _('instrument mappings')
        permissions = [
            ('view_instrumentmapping', 'Can view instrument mapping'),
            ('manage_instrumentmapping', 'Can manage instrument mapping'),
        ]

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class InstrumentAttributeMapping(models.Model):
    mapping = models.ForeignKey(InstrumentMapping, related_name='attributes')
    attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', null=True, blank=True)
    name = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH)

    class Meta:
        abstract = True
        unique_together = (
            ('mapping', 'attribute_type')
        )

    def __str__(self):
        return '%s -> %s' % (self.external_name, self.attribute_type)


@python_2_unicode_compatible
class BloombergRequestLogEntry(TimeStampedModel):
    master_user = models.ForeignKey('users.MasterUser')
    member = models.ForeignKey('users.Member')

    request_id = models.CharField(max_length=36)
    request = models.TextField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)

    is_success = models.NullBooleanField()
    is_user_got_response = models.NullBooleanField()

    class Meta:
        abstract = True
        index_together = (
            ('master_user', 'request_id')
        )

    def __str__(self):
        return '%s' % self.request_id
