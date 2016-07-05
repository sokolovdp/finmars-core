import json

from django.utils.encoding import force_text


def send(recipients, message=None, actor=None, verb=None, action_object=None, target=None, data=None, throttle=False):
    from poms.notifications.models import Notification
    from poms.notifications.throttling import allow_notification

    if throttle and not allow_notification():
        return

    ret = []
    for recipient in recipients:
        n = Notification.objects.create(
            recipient=recipient,
            message=message,
            actor=actor,
            verb=force_text(verb),
            action_object=action_object,
            target=target,
            data=json.dumps(data, sort_keys=True) if data else None,
        )
        ret.append(n)
    return ret

# def debug(*args, **kwargs):
#     kwargs['level'] = constants.DEBUG
#     send(*args, **kwargs)
#
#
# def info(*args, **kwargs):
#     kwargs['level'] = constants.INFO
#     send(*args, **kwargs)
#
#
# def success(*args, **kwargs):
#     kwargs['level'] = constants.SUCCESS
#     send(*args, **kwargs)
#
#
# def warning(*args, **kwargs):
#     kwargs['level'] = constants.WARNING
#     send(*args, **kwargs)
#
#
# def error(*args, **kwargs):
#     kwargs['level'] = constants.ERROR
#     send(*args, **kwargs)
