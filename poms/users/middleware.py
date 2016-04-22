from django.utils.functional import SimpleLazyObject


class AuthenticationMiddleware(object):
    def process_request(self, request):
        from poms.users.utils import get_master_user, get_member

        # TODO: not worked for rest basic and token authentication
        request.user.master_user = SimpleLazyObject(lambda: get_master_user(request))
        request.user.member = SimpleLazyObject(lambda: get_member(request))
