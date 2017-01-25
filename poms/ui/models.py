import json

from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import ugettext_lazy

from poms.users.models import MasterUser, Member


class BaseLayout(models.Model):
    content_type = models.ForeignKey(ContentType, verbose_name=ugettext_lazy('content type'))
    json_data = models.TextField(null=True, blank=True, verbose_name=ugettext_lazy('json data'))

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
    master_user = models.ForeignKey(MasterUser, related_name='template_list_layouts',
                                    verbose_name=ugettext_lazy('master user'))
    name = models.CharField(max_length=255, blank=True, default="", db_index=True, verbose_name=ugettext_lazy('name'))
    is_default = models.BooleanField(default=False, verbose_name=ugettext_lazy('is default'))

    class Meta(BaseLayout.Meta):
        unique_together = [
            ['master_user', 'content_type', 'name'],
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.is_default:
            qs = TemplateListLayout.objects.filter(master_user=self.master_user, content_type=self.content_type,
                                                   is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_default=False)
        return super(TemplateListLayout, self).save(*args, **kwargs)


class TemplateEditLayout(BaseLayout):
    master_user = models.ForeignKey(MasterUser, related_name='edit_layouts', verbose_name=ugettext_lazy('master user'))

    class Meta(BaseLayout.Meta):
        unique_together = [
            ['master_user', 'content_type'],
        ]
        ordering = ['content_type']


class ListLayout(BaseLayout):
    member = models.ForeignKey(Member, related_name='template_list_layouts', verbose_name=ugettext_lazy('member'))
    name = models.CharField(max_length=255, blank=True, default="", db_index=True, verbose_name=ugettext_lazy('name'))
    is_default = models.BooleanField(default=False, verbose_name=ugettext_lazy('is default'))

    class Meta(BaseLayout.Meta):
        unique_together = [
            ['member', 'content_type', 'name'],
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.is_default:
            qs = ListLayout.objects.filter(member=self.member, content_type=self.content_type, is_default=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_default=False)
        return super(ListLayout, self).save(*args, **kwargs)


class EditLayout(BaseLayout):
    member = models.ForeignKey(Member, related_name='edit_layouts', verbose_name=ugettext_lazy('member'))

    class Meta(BaseLayout.Meta):
        unique_together = [
            ['member', 'content_type'],
        ]
        ordering = ['content_type']

# history.register(TemplateListLayout)
# history.register(TemplateEditLayout)
# history.register(ListLayout)
# history.register(EditLayout)
