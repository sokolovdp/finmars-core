import json

from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from poms.audit import history
from poms.users.models import MasterUser, Member


class BaseLayout(models.Model):
    content_type = models.ForeignKey(ContentType)
    json_data = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True

    def get_data(self):
        try:
            return json.loads(self.json_data) if self.json_data else None
        except (ValueError, TypeError):
            return None

    def set_data(self, data):
        self.json_data = json.dumps(data, cls=DjangoJSONEncoder, sort_keys=True) if data else None

    data = property(get_data, set_data)


class TemplateListLayout(BaseLayout):
    master_user = models.ForeignKey(MasterUser)
    name = models.CharField(max_length=255, blank=True, default="", db_index=True)

    class Meta:
        unique_together = [
            ['master_user', 'content_type', 'name'],
        ]


class TemplateEditLayout(BaseLayout):
    master_user = models.ForeignKey(MasterUser)

    class Meta:
        unique_together = [
            ['master_user', 'content_type'],
        ]


class ListLayout(BaseLayout):
    member = models.ForeignKey(Member)
    name = models.CharField(max_length=255, blank=True, default="", db_index=True)

    class Meta:
        unique_together = [
            ['member', 'content_type', 'name'],
        ]


class EditLayout(BaseLayout):
    member = models.ForeignKey(Member)

    class Meta:
        unique_together = [
            ['member', 'content_type'],
        ]


# history.register(TemplateListLayout)
# history.register(TemplateEditLayout)
# history.register(ListLayout)
# history.register(EditLayout)
