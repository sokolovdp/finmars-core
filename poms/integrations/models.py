from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.audit import history
from poms.common.models import TimeStampedModel

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
        index_together = (
            ('master_user', 'mapping_name')
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
        unique_together = (
            ('mapping', 'attribute_type')
        )
        ordering = ('attribute_type__name',)

    def __str__(self):
        return '%s -> %s' % (self.name, self.attribute_type)


@python_2_unicode_compatible
class BloombergRequestLogEntry(TimeStampedModel):
    master_user = models.ForeignKey('users.MasterUser')
    member = models.ForeignKey('users.Member')

    token = models.CharField(max_length=36, null=True, blank=True, db_index=True)
    is_success = models.NullBooleanField(db_index=True)
    is_user_got_response = models.NullBooleanField(db_index=True)

    request_id = models.CharField(max_length=36, null=True, blank=True, db_index=True)
    request = models.TextField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('bloomberg request log')
        verbose_name_plural = _('bloomberg request logs')
        ordering = ('created',)

    def __str__(self):
        return '%s' % self.request_id


history.register(InstrumentMapping, follow=['attributes'])
history.register(InstrumentAttributeMapping)
