from logging import getLogger

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone

from poms.integrations.models import PricingAutomatedSchedule

_l = getLogger('poms.integrations')



# @receiver(pre_save, dispatch_uid='pricing_automated_schedule_reschedule', sender=PricingAutomatedSchedule)
# def pricing_automated_schedule_reschedule(sender, instance=None, **kwargs):
#     # from djcelery.models import CrontabSchedule, PeriodicTask
#     if instance.is_enabled and instance.next_run_at < timezone.now():
#         instance.schedule(save=False)
