from __future__ import unicode_literals

from django.db.models.signals import post_save
from django.dispatch import receiver

from poms import notifications
from poms.chats.models import Message, DirectMessage
from poms.common.middleware import get_request
from poms.obj_perms.utils import has_view_perms
from poms.users.models import Member


@receiver(post_save, dispatch_uid='chat_message_created', sender=Message)
def chat_message_created(sender, instance=None, created=None, **kwargs):
    if created:
        # me = get_request().user.member
        master_user = instance.thread.master_user
        thread = instance.thread
        qs = Member.objects.filter(master_user=master_user).exclude(id=instance.sender_id)
        recipients = [m.user for m in qs if has_view_perms(m, thread)]
        notifications.send(recipients,
                           actor=instance.sender,
                           verb='sent',
                           action_object=instance,
                           target=instance.thread)


@receiver(post_save, dispatch_uid='direct_chat_message_created', sender=DirectMessage)
def direct_chat_message_created(sender, instance=None, created=None, **kwargs):
    if created and instance.sender_id != instance.recipient_id:
        notifications.send([instance.recipient.user],
                           actor=instance.sender,
                           verb='sent',
                           action_object=instance)
