from django.db import models


class InstrumentMapping(models.Model):
    master_user = models.ForeignKey('users.MasterUser')
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True
        index_together = (
            ('mapping', 'external_name')
        )


class InstrumentMappingItem(models.Model):
    BASIC_ATTRIBUTE_CHOICES = (
        ('user_code', 'user_code'),
        ('name', 'name'),
        ('short_name', 'short_name'),
        ('public_name', 'public_name'),
        ('notes', 'notes'),
        ('instrument_type', 'instrument_type'),
        ('pricing_currency', 'pricing_currency'),
        ('price_multiplier', 'price_multiplier'),
        ('accrued_currency', 'accrued_currency'),
        ('accrued_multiplier', 'accrued_multiplier'),
        ('daily_pricing_model', 'daily_pricing_model'),
        ('payment_size_detail', 'payment_size_detail'),
        ('default_price', 'default_price'),
        ('default_accrued', 'default_accrued'),
        ('price_download_mode', 'price_download_mode'),
    )

    mapping = models.ForeignKey(InstrumentMapping)
    external_name = models.CharField(max_length=255)
    basic_attribute = models.CharField(max_length=50, null=True, blank=True, choices=BASIC_ATTRIBUTE_CHOICES)
    dynamic_attribute = models.ForeignKey('instruments.InstrumentAttributeType', null=True, blank=True)

    class Meta:
        abstract = True
        index_together = (
            ('mapping', 'external_name')
        )
