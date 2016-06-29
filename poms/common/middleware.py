# coding=utf-8
from __future__ import unicode_literals

import ipaddress
from threading import local

from django.conf import settings


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

    if settings.DEBUG:
        ip = ipaddress.ip_address(user_ip)
        if ip.is_private or ip.is_reserved:
            # user_ip_source = 'X_FORWARDED_FOR'
            # user_ip_source = 'X_REAL_IP'
            user_ip_source = 'REMOTE_ADDR'
            # user_ip = '95.165.168.246'  # москва
            # user_ip = '195.19.204.76' # питер
            # user_ip = '77.221.130.2' # норильск
            # user_ip = '93.88.13.132' # владивосток
            # user_ip = '8.8.8.8'
            # user_ip = '185.76.80.1'
            # user_ip = '91.219.220.8' # Ukraine
            user_ip = '128.199.165.82' # Singapore

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
