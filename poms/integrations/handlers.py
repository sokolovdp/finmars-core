import json
from logging import getLogger

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from poms.integrations.models import PricingAutomatedSchedule
from poms.integrations.tasks import download_pricing_auto

_l = getLogger('poms.integrations')


def get_pricing_automated_schedule_task_name(master_user_id):
    return 'download_pricing_auto_%s' % master_user_id


def pricing_auto_cancel(master_user_id):
    from djcelery.models import PeriodicTask

    task_name = get_pricing_automated_schedule_task_name(master_user_id)
    _l.info('pricing auto cancel: master_user=%s, task_name=%s', master_user_id, task_name)
    PeriodicTask.objects.filter(name=task_name).delete()


@receiver(post_save, dispatch_uid='pricing_automated_schedule_reschedule', sender=PricingAutomatedSchedule)
def pricing_automated_schedule_reschedule(sender, instance=None, **kwargs):
    from djcelery.models import CrontabSchedule, PeriodicTask

    task_name = get_pricing_automated_schedule_task_name(instance.master_user_id)
    if instance.is_enabled and instance.cron_expr:
        _l.info('pricing automated schedule: master_user=%s, is_enabled=%s', instance.master_user_id,
                instance.is_enabled)
        v = CrontabSchedule.from_schedule(instance.to_crontab())
        cs, created = CrontabSchedule.objects.get_or_create(minute=v.minute, hour=v.hour, day_of_week=v.day_of_week,
                                                            day_of_month=v.day_of_month, month_of_year=v.month_of_year,
                                                            defaults={})
        try:
            pt = PeriodicTask.objects.get(name=task_name)
            pt.crontab = cs
            pt.enabled = True
            pt.save(update_fields=['crontab', 'enabled'])
        except PeriodicTask.DoesNotExist:
            task_params = {
                'master_user_id': instance.master_user_id
            }
            pt = PeriodicTask()
            pt.name = task_name
            pt.crontab = cs
            pt.enabled = True
            pt.task = download_pricing_auto.name
            pt.kwargs = json.dumps(task_params)
            pt.save()
    else:
        pricing_auto_cancel(instance.master_user_id)


@receiver(post_delete, dispatch_uid='pricing_automated_schedule_cancel', sender=PricingAutomatedSchedule)
def pricing_automated_schedule_cancel(sender, instance=None, **kwargs):
    pricing_auto_cancel(instance.master_user_id)
