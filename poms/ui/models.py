from django.contrib.contenttypes.models import ContentType
from django.db import models

from poms.audit import history
from poms.users.models import MasterUser, Member


class TemplateListLayout(models.Model):
    master_user = models.ForeignKey(MasterUser)
    content_type = models.ForeignKey(ContentType)
    name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    json_data = models.TextField(null=False, blank=True, default="")

    class Meta:
        unique_together = [
            ['master_user', 'content_type', 'name'],
        ]


class TemplateEditLayout(models.Model):
    master_user = models.ForeignKey(MasterUser)
    content_type = models.ForeignKey(ContentType)
    json_data = models.TextField(null=False, blank=True, default="")

    class Meta:
        unique_together = [
            ['master_user', 'content_type'],
        ]


class ListLayout(models.Model):
    member = models.ForeignKey(Member)
    content_type = models.ForeignKey(ContentType)
    name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    json_data = models.TextField(null=False, blank=True, default="")

    class Meta:
        unique_together = [
            ['member', 'content_type', 'name'],
        ]


class EditLayout(models.Model):
    member = models.ForeignKey(Member)
    content_type = models.ForeignKey(ContentType)
    json_data = models.TextField(null=False, blank=True, default="")

    class Meta:
        unique_together = [
            ['member', 'content_type'],
        ]


history.register(TemplateListLayout)
history.register(TemplateEditLayout)
history.register(ListLayout)
history.register(EditLayout)
