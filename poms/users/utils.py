from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound

from poms.users.models import Member


def get_master_user(request, master_user_id=None):
    user = request.user
    if hasattr(user, '_cached_master_user'):
        return user._cached_master_user
    if master_user_id is None:
        master_user_id = request.GET.get('master_user_id', None)
    if master_user_id is None:
        master_user_id = request.session.get('master_user_id', None)
    try:
        if master_user_id is None:
            if settings.DEV:
                member = user.members.first()
                master_user = member.master_user
            else:
                raise NotFound()
        else:
            master_user = user.members.get(pk=master_user_id)
        user._cached_master_user = master_user
        return master_user
    except ObjectDoesNotExist:
        raise NotFound()


def set_master_user(request, master_user_id):
    old_master_user_id = request.session.get('master_user_id', None)
    if old_master_user_id != master_user_id:
        if master_user_id is None:
            del request.session['master_user_id']
        else:
            request.session['master_user_id'] = master_user_id


def get_member(request, master_user_id=None):
    user = request.user
    if hasattr(user, '_cached_member'):
        return user._cached_member
    try:
        master_user = get_master_user(request, master_user_id)
        master_user_id = master_user.id
        member = Member.objects.get(user=request.user, master_user=master_user_id)
        user._cached_member = member
        return member
    except ObjectDoesNotExist:
        raise NotFound()


def is_admin(request, master_user_id=None):
    try:
        member = get_member(request, master_user_id)
        return member.is_admin
    except NotFound:
        return False


def is_owner(request, master_user_id=None):
    try:
        member = get_member(request, master_user_id)
        return member.is_admin
    except NotFound:
        return False


def is_admin_role(request, master_user_id=None):
    try:
        member = get_member(request, master_user_id)
        return member.is_admin or member.is_owner
    except NotFound:
        return False