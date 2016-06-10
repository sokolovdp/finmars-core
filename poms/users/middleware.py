from django.utils import timezone, translation
from django.utils.functional import SimpleLazyObject


class AuthenticationMiddleware(object):
    def process_request(self, request):
        from poms.users.utils import get_master_user, get_member

        # TODO: not worked for rest basic and token authentication
        request.user.master_user = SimpleLazyObject(lambda: get_master_user(request))
        request.user.member = SimpleLazyObject(lambda: get_member(request))


class LocaleMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated:
            if request.user.profile.language:
                translation.activate(request.user.profile.language)
                request.LANGUAGE_CODE = translation.get_language()


class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated:
            master_user = request.user.master_user
            if master_user.timezone:
                timezone.activate(master_user.timezone)
            else:
                timezone.deactivate()
