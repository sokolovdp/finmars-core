import json

from django.utils.encoding import force_text

from poms.notifications import constants


def add(recipients, level=constants.INFO, type=None, message=None,
        actor=None, verb=None, target=None, action_object=None, data=None):
    from poms.notifications.models import Notification

    ret = []
    for recipient in recipients:
        n = Notification.objects.create(
            recipient=recipient,
            level=level,
            type=type,
            message=message,
            actor=actor,
            verb=force_text(verb),
            target=target,
            action_object=action_object,
            data=json.dumps(data, sort_keys=True) if data else None,
        )
        ret.append(n)
    return ret


def debug(*args, **kwargs):
    kwargs['level'] = constants.DEBUG
    add(*args, **kwargs)


def info(*args, **kwargs):
    kwargs['level'] = constants.INFO
    add(*args, **kwargs)


def success(*args, **kwargs):
    kwargs['level'] = constants.SUCCESS
    add(*args, **kwargs)


def warning(*args, **kwargs):
    kwargs['level'] = constants.WARNING
    add(*args, **kwargs)


def error(*args, **kwargs):
    kwargs['level'] = constants.ERROR
    add(*args, **kwargs)
