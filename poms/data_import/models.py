from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.db import models
from django.dispatch import receiver
from datetime import datetime
from .tasks import run_import
from poms.users.models import MasterUser


class DataImportSchema(models.Model):
    model = models.ForeignKey(ContentType)
    name = models.CharField(max_length=100, unique=True)


class DataImport(models.Model):
    STATUS = (
        (0, 'READY'),
        (1, 'IN PROGRESS'),
        (2, 'DONE'),
        (3, 'FAIL'),
    )
    master_user = models.ForeignKey(MasterUser, blank=True, null=True)
    schema = models.ForeignKey(DataImportSchema)
    file = models.FileField(upload_to='import/')
    status = models.IntegerField(choices=STATUS, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # def __str__(self):
    #     return self.model.model + '/' + datetime.strftime(self.modified_at, '%Y-%m-%d')


class DataImportSchemaFields(models.Model):
    schema = models.ForeignKey(DataImportSchema)
    source = models.CharField(max_length=100)
    target = models.CharField(max_length=100)


@receiver(post_save, sender=DataImport)
def update_state(sender, instance, *args, **kwargs):
    if instance.status == 1:
        run_import(instance)
    if DataImportSchema.objects.filter(data_import=instance):
        instance.status = 1
        instance.save()
    #     run_import.delay(instance)
