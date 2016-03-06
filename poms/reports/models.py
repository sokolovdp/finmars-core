from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType

from poms.users.models import MasterUser


# @python_2_unicode_compatible
# class ReportType(models.Model):
#     code = models.CharField(max_length=50, verbose_name=_('code'))
#     name = models.CharField(max_length=255, verbose_name=_('name'))
#     description = models.TextField(null=True, blank=True, default='', verbose_name=_('description'))
#
#     class Meta:
#         verbose_name = _('report type')
#         verbose_name_plural = _('report types')
#
#     def __str__(self):
#         return '%s' % (self.name,)
#
#
# @python_2_unicode_compatible
# class Mapping(models.Model):
#     master_user = models.ForeignKey(MasterUser, related_name='report_mappings', verbose_name=_('master user'))
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.CharField(max_length=255)
#     content_object = GenericForeignKey('content_type', 'object_id')
#     name = models.CharField(max_length=255, verbose_name=_('object attribute'))
#     expr = models.TextField(null=True, blank=True, verbose_name=_('expression'))
#
#     class Meta:
#         verbose_name = _('mapping')
#         verbose_name_plural = _('mappings')
#
#     def __str__(self):
#         return '%s #%s - %s' % (self.content_type, self.object_id, self.name)
