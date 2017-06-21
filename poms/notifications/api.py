import json

from django.utils.encoding import force_text


def send(recipients, message=None, actor=None, verb=None, action_object=None, target=None, data=None, throttle=False):
    from poms.users.models import Member
    from poms.notifications.models import Notification
    from poms.notifications.throttling import allow_notification

    ret = []

    if not recipients:
        return ret

    if throttle and not allow_notification():
        return ret

    for member_or_user in recipients:
        if isinstance(member_or_user, Member):
            if member_or_user.is_deleted:
                continue
            recipient = member_or_user.user
            recipient_member = member_or_user
        else:
            recipient = member_or_user
            recipient_member = None
        n = Notification()
        n.recipient = recipient
        n.recipient_member = recipient_member
        n.message = message
        n.actor = actor
        n.verb = force_text(verb)
        n.action_object = action_object
        n.target = target
        n.data = json.dumps(data, sort_keys=True) if data else None
        n.save()
        ret.append(n)

    return ret


def _send_instance_action_message(master_user, member, instance, verb, check_perms=False):
    from poms.obj_perms.utils import has_any_perms

    recipients = []
    for member in master_user.members.all():
        if member.is_deleted or member.user_id is None:
            continue
        if check_perms and not has_any_perms(member, instance):
            continue
        recipients.append(member)
    if recipients:
        send(recipients, actor=member, verb=verb, action_object=instance)


def send_instance_created(master_user, member, instance, check_perms=False):
    _send_instance_action_message(master_user=master_user, member=member, instance=instance, verb='created',
                                  check_perms=check_perms)


def send_instance_changed(master_user, member, instance, check_perms=False):
    _send_instance_action_message(master_user=master_user, member=member, instance=instance, verb='changed',
                                  check_perms=check_perms)


def send_instance_deleted(master_user, member, instance, check_perms=False):
    _send_instance_action_message(master_user=master_user, member=member, instance=instance, verb='deleted',
                                  check_perms=check_perms)
