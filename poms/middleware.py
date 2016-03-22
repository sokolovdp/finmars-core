from __future__ import unicode_literals

import ipaddress
from threading import local


def get_ip(request):
    user_ip = None

    ips = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if ips:
        if ',' in ips:
            ips = [ip.strip() for ip in ips.split(',')]
        else:
            ips = [ips.strip()]
        for ip in ips:
            try:
                ip = ipaddress.ip_address(ip)
            except ValueError:
                pass
            else:
                if ip.is_private:
                    continue
                else:
                    user_ip = str(ip)
                    break

    if user_ip is None:
        ip = request.META.get('HTTP_X_REAL_IP', '')
        if ip:
            try:
                ip = ipaddress.ip_address(ip)
            except ValueError:
                pass
            else:
                if ip.is_private:
                    pass
                else:
                    user_ip = str(ip)

    if user_ip is None:
        ip = request.META.get('REMOTE_ADDR', '')
        if ip:
            try:
                ip = ipaddress.ip_address(ip)
            except ValueError:
                pass
            else:
                if ip.is_private:
                    user_ip = str(ip)
                else:
                    user_ip = str(ip)

    if not user_ip:
        user_ip = '127.0.0.1'

    return user_ip


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', None)


_active = local()


def activate(request):
    _active.request = request


def deactivate():
    if hasattr(_active, "request"):
        del _active.request


def get_request():
    request = getattr(_active, "request", None)
    # assert request is not None, "CommonMiddleware is not installed"
    return request
    # if hasattr(_active, "request"):
    #     return _active.request
    # raise RuntimeError('request not found')


class CommonMiddleware(object):
    def process_request(self, request):
        request.user_ip = get_ip(request)
        request.user_agent = get_user_agent(request)
        activate(request)

    def process_response(self, request, response):
        deactivate()
        return response
