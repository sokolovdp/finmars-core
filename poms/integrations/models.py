from __future__ import unicode_literals, print_function

import json
import uuid
from datetime import date, datetime

import six
from dateutil import parser
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from poms.common import formula
from poms.common.models import TimeStampedModel
from poms.instruments.models import Instrument, InstrumentAttribute
from poms.integrations.storage import bloomberg_cert_storage
from poms.obj_attrs.models import AbstractAttributeType

MAPPING_FIELD_MAX_LENGTH = 32


@python_2_unicode_compatible
class InstrumentMapping(models.Model):
    BASIC_FIELDS = ['user_code', 'name', 'short_name', 'public_name', 'notes', 'instrument_type',
                    'pricing_currency', 'price_multiplier', 'accrued_currency', 'accrued_multiplier',
                    'daily_pricing_model', 'payment_size_detail', 'default_price', 'default_accrued',
                    'user_text_1', 'user_text_2', 'user_text_3', 'price_download_mode', ]

    master_user = models.ForeignKey('users.MasterUser')
    mapping_name = models.CharField(max_length=255)

    user_code = models.CharField(max_length=255, blank=True, default='')
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    public_name = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)
    notes = models.CharField(max_length=MAPPING_FIELD_MAX_LENGTH, null=True, blank=True)

    instrument_type = models.CharField(max_length=255, blank=True, default='')
    pricing_currency = models.CharField(max_length=255, blank=True, default='')
    price_multiplier = models.CharField(max_length=255, blank=True, default='1.0')
    accrued_currency = models.CharField(max_length=255, blank=True, default='')
    accrued_multiplier = models.CharField(max_length=255, blank=True, default='1.0')
    daily_pricing_model = models.CharField(max_length=255, blank=True, default='')
    payment_size_detail = models.CharField(max_length=255, blank=True, default='')
    default_price = models.CharField(max_length=255, blank=True, default='0.0')
    default_accrued = models.CharField(max_length=255, blank=True, default='0.0')
    user_text_1 = models.CharField(max_length=255, blank=True, default='')
    user_text_2 = models.CharField(max_length=255, blank=True, default='')
    user_text_3 = models.CharField(max_length=255, blank=True, default='')
    price_download_mode = models.CharField(max_length=255, blank=True, default='')

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
        return self.mapping_name

    def clean_mapping(self, name):
        if name is None:
            return None
        return name.strip()

    # @property
    # def mapping_fields(self):
    #     f = set()
    #
    #     def add(n):
    #         n = self.clean_mapping(n)
    #         if n:
    #             f.add(n)
    #
    #     for attr in self.BASIC_FIELDS:
    #         add(getattr(self, attr))
    #
    #     for attr in self.attributes.all():
    #         add(attr.name)
    #
    #     return f

    def create_instrument(self, values, save=True):
        instr = Instrument(master_user=self.master_user)

        instr.instrument_type = self.master_user.instrument_type
        instr.pricing_currency = self.master_user.currency
        instr.accrued_currency = self.master_user.currency

        def get_date(v):
            if v is not None:
                if isinstance(v, date):
                    return v
                elif isinstance(v, datetime):
                    return v.date()
                else:
                    v = parser.parse(v)
                    if v:
                        return v.date()
            return None

        def get_num(v):
            if v is not None:
                return float(v)
            return None

        for attr in self.BASIC_FIELDS:
            expr = getattr(self, attr)
            if expr:
                v = formula.safe_eval(expr, names=values)
                if attr in ['pricing_currency', 'accrued_currency']:
                    if v:
                        v = self.master_user.currencies.get(user_code=v)
                        setattr(instr, attr, v)
                elif attr in ['instrument_type']:
                    if v:
                        v = self.master_user.instrument_types.get(user_code=v)
                        setattr(instr, attr, v)
                elif attr in ['price_multiplier', 'accrued_multiplier', 'default_price', 'default_accrued']:
                    v = get_num(v)
                    setattr(instr, attr, v)
                else:
                    v = six.text_type(v)
                    setattr(instr, attr, v)

        if save:
            instr.save()

        iattrs = []
        for attr in self.attributes.select_related('attribute_type').all():
            tattr = attr.attribute_type

            iattr = InstrumentAttribute(content_object=instr, attribute_type=tattr)
            iattrs.append(iattr)

            if attr.value:
                v = formula.safe_eval(attr.value, names=values)
                if tattr.value_type == AbstractAttributeType.STRING:
                    iattr.value_string = six.text_type(v)
                elif tattr.value_type == AbstractAttributeType.NUMBER:
                    iattr.value_float = get_num(v)
                elif tattr.value_type == AbstractAttributeType.DATE:
                    iattr.value_date = get_date(v)
                elif tattr.value_type == AbstractAttributeType.CLASSIFIER:
                    v = six.text_type(v)
                    v = tattr.classifiers.filter(name=v).first()
                    iattr.classifier = v

            if save:
                iattr.save()

        instr.attributes_preview = iattrs
        # if not preview:
        #     instr.attributes = iattrs

        return instr


class InstrumentMappingInput(models.Model):
    mapping = models.ForeignKey(InstrumentMapping, related_name='inputs')
    name = models.CharField(max_length=32)

    class Meta:
        unique_together = (
            ('mapping', 'name')
        )
        ordering = ('name',)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class InstrumentMappingAttribute(models.Model):
    mapping = models.ForeignKey(InstrumentMapping, related_name='attributes')
    attribute_type = models.ForeignKey('instruments.InstrumentAttributeType', null=True, blank=True)
    value = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        unique_together = (
            ('mapping', 'attribute_type')
        )
        ordering = ('attribute_type__name',)

    def __str__(self):
        # return '%s -> %s' % (self.name, self.attribute_type)
        return '%s' % (self.attribute_type,)


def bloomberg_cert_upload_to(instance, filename):
    # return '%s/%s' % (instance.master_user_id, filename)
    return '%s/%s' % (instance.master_user_id, uuid.uuid4().hex)


class BloombergConfig(models.Model):
    master_user = models.OneToOneField('users.MasterUser', related_name='bloomberg_config')
    p12cert = models.FileField(null=True, blank=True, upload_to=bloomberg_cert_upload_to,
                               storage=bloomberg_cert_storage)
    password = models.CharField(max_length=64, null=True, blank=True)
    cert = models.FileField(null=True, blank=True, upload_to=bloomberg_cert_upload_to, storage=bloomberg_cert_storage)
    key = models.FileField(null=True, blank=True, upload_to=bloomberg_cert_upload_to, storage=bloomberg_cert_storage)

    class Meta:
        verbose_name = _('bloomberg config')
        verbose_name_plural = _('bloomberg configs')

    def __str__(self):
        return '%s' % self.master_user

    # def delete(self, using=None, keep_parents=False):
    #     if self.p12cert:
    #         self.p12cert.delete(save=False)
    #     if self.cert:
    #         self.cert.delete(save=False)
    #     if self.key:
    #         self.key.delete(save=False)
    #     super(BloombergConfig, self).delete(using=using, keep_parents=keep_parents)

    @property
    def pair(self):
        if self.cert and self.key:
            return self.cert, self.key
        elif self.p12cert:
            from poms.integrations.providers.bloomberg import get_certs
            return get_certs(self.p12cert.read(), self.password, is_base64=False)
        return None, None

    @property
    def has_p12cert(self):
        return bool(self.p12cert)

    @property
    def has_password(self):
        return bool(self.password)

    @property
    def has_cert(self):
        return bool(self.cert)

    @property
    def has_key(self):
        return bool(self.key)

    @property
    def is_ready(self):
        return (self.has_p12cert and self.has_password) or (self.has_cert and self.has_key)


@python_2_unicode_compatible
class BloombergTask(TimeStampedModel):
    ACTION_INSTRUMENT = 'instrument'
    ACTION_PRICING_LATEST = 'pricing_latest'
    ACTION_PRICE_HISTORY = 'pricing_history'

    STATUS_PENDING = 0
    STATUS_REQUEST_SENT = 1
    STATUS_WAIT_RESPONSE = 2
    STATUS_DONE = 3
    STATUS_ERROR = -1
    STATUS_TIMEOUT = -2
    STATUS_CHOICES = (
        (STATUS_PENDING, 'STATUS_PENDING'),
        (STATUS_REQUEST_SENT, 'STATUS_REQUEST_SENT'),
        (STATUS_WAIT_RESPONSE, 'STATUS_WAIT_RESPONSE'),
        (STATUS_DONE, 'STATUS_DONE'),
        (STATUS_ERROR, 'STATUS_ERROR'),
        (STATUS_TIMEOUT, 'STATUS_TIMEOUT'),
    )

    master_user = models.ForeignKey('users.MasterUser', related_name='bloomberg_tasks')
    member = models.ForeignKey('users.Member', related_name='bloomberg_tasks', null=True, blank=True)

    status = models.SmallIntegerField(default=STATUS_PENDING, choices=STATUS_CHOICES)

    action = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    response_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    kwargs = models.TextField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('bloomberg task')
        verbose_name_plural = _('bloomberg tasks')
        ordering = ('-created',)

    def __str__(self):
        return '%s' % self.id

    @property
    def kwargs_object(self):
        return json.loads(self.kwargs)

    @property
    def result_object(self):
        return json.loads(self.result)
