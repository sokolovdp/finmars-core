from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import NotFound, PermissionDenied

from poms.users.models import Member, MasterUser


def get_master_user(request):
    user = request.user
    if not user.is_authenticated:
        raise PermissionDenied()

    master_user_id = request.GET.get('master_user_id', None)
    if master_user_id is None:
        master_user_id = request.session.get('master_user_id', None)

    try:
        if master_user_id is None:
            if settings.DEV:
                member = user.members.select_related('master_user').first()
                return member.master_user
        if master_user_id:
            return MasterUser.objects.get(id=master_user_id, members__user=user)
        raise NotFound()
    except ObjectDoesNotExist:
        raise NotFound()


def set_master_user(request, master_user):
    master_user_id = master_user.id
    old_master_user_id = request.session.get('master_user_id', None)
    if old_master_user_id != master_user_id:
        if master_user_id is None:
            del request.session['master_user_id']
        else:
            request.session['master_user_id'] = master_user_id


def get_member(request):
    user = request.user
    if not user.is_authenticated:
        raise PermissionDenied()
    master_user = user.master_user
    try:
        # for member in master_user.members.all():
        #     if member.master_user_id == master_user.id:
        #         return member
        # raise NotFound()
        # member = Member.objects.get(user=user, master_user=master_user)
        member = master_user.members.select_related('master_user').prefetch_related('groups').get(user=request.user)
        return member
    except ObjectDoesNotExist:
        raise NotFound()


# def is_admin(request, master_user_id=None):
#     try:
#         member = get_member(request)
#         return member.is_admin
#     except NotFound:
#         return False
#
#
# def is_owner(request, master_user_id=None):
#     try:
#         member = get_member(request, master_user_id)
#         return member.is_admin
#     except NotFound:
#         return False
#
#
# def is_admin_role(request, master_user_id=None):
#     try:
#         member = get_member(request, master_user_id)
#         return member.is_admin or member.is_owner
#     except NotFound:
#         return False