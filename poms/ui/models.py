import json

from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from poms.users.models import MasterUser, Member


class BaseLayout(models.Model):
    content_type = models.ForeignKey(ContentType)
    json_data = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def data(self):
        try:
            return json.loads(self.json_data) if self.json_data else None
        except (ValueError, TypeError):
            return None

    @data.setter
    def data(self, data):
        self.json_data = json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True) if data else None


class TemplateListLayout(BaseLayout):
    master_user = models.ForeignKey(MasterUser, related_name='template_list_layouts')
    name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ['master_user', 'content_type', 'name'],
        ]

    def save(self, *args, **kwargs):
        if self.is_default:
            qs = TemplateListLayout.objects.filter(master_user=self.master_user, content_type=self.content_type,
                                                   is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_default=False)
        return super(TemplateListLayout, self).save(*args, **kwargs)


class TemplateEditLayout(BaseLayout):
    master_user = models.ForeignKey(MasterUser, related_name='edit_layouts')

    class Meta:
        unique_together = [
            ['master_user', 'content_type'],
        ]


class ListLayout(BaseLayout):
    member = models.ForeignKey(Member, related_name='template_list_layouts')
    name = models.CharField(max_length=255, blank=True, default="", db_index=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ['member', 'content_type', 'name'],
        ]

    def save(self, *args, **kwargs):
        if self.is_default:
            qs = ListLayout.objects.filter(member=self.member, content_type=self.content_type, is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_default=False)
        return super(ListLayout, self).save(*args, **kwargs)


class EditLayout(BaseLayout):
    member = models.ForeignKey(Member, related_name='edit_layouts')

    class Meta:
        unique_together = [
            ['member', 'content_type'],
        ]

# history.register(TemplateListLayout)
# history.register(TemplateEditLayout)
# history.register(ListLayout)
# history.register(EditLayout)
