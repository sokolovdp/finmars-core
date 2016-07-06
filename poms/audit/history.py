from __future__ import unicode_literals

import json
from threading import local

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.utils.decorators import ContextDecorator
from django.utils.encoding import force_text
from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
from reversion import revisions as reversion
from reversion.errors import RevisionManagementError


_active = local()


def activate():
    _active.value = True


def deactivate():
    if hasattr(_active, "value"):
        del _active.value


def is_active():
    return getattr(_active, "value", False)


class enable(ContextDecorator):
    def __enter__(self):
        activate()

    def __exit__(self, exc_type, exc_value, traceback):
        deactivate()


def is_historical_proxy(obj):
    return isinstance(obj, ModelProxy)


def register(model, **kwargs):
    reversion.register(model, **kwargs)


def add_comment(message):
    # try:
    #     comment = reversion.get_comment()
    #     if comment:
    #         comment += ' ' + message
    #     else:
    #         comment = message
    #     reversion.set_comment(comment)
    # except RevisionManagementError:
    #     pass
    try:
        comment = reversion.get_comment()
        if comment:
            try:
                comment = json.loads(comment)
            except ValueError:
                comment = []
        else :
            comment = []
        ctype = message['content_type']
        message['content_type'] = '%s.%s' % (ctype.app_label, ctype.model)
        comment.append(message)
        reversion.set_comment(json.dumps(comment))
    except RevisionManagementError:
        pass


def object_added(obj):
    if is_active():
        # message = _('Added %(name)s "%(object)s".') % {
        #     'name': force_text(obj._meta.verbose_name),
        #     'object': force_text(obj)
        # }
        # add_comment(message)
        add_comment({
            'action': 'add',
            'object_name': force_text(obj._meta.verbose_name),
            'object_repr': force_text(obj),
            'content_type': ContentType.objects.get_for_model(obj),
            'object_id': obj.id,
        })


def object_changed(obj, fields):
    if is_active():
        # message = _('Changed %(list)s for %(name)s "%(object)s".') % {
        #     'list': get_text_list(fields, _('and')),
        #     'name': force_text(obj._meta.verbose_name),
        #     'object': force_text(obj)
        # }
        # add_comment(message)
        add_comment({
            'action': 'change',
            'object_name': force_text(obj._meta.verbose_name),
            'object_repr': force_text(obj),
            'fields': fields,
            'content_type': ContentType.objects.get_for_model(obj),
            'object_id': obj.id,
        })


def object_deleted(obj):
    if is_active():
        # message = _('Deleted %(name)s "%(object)s".') % {
        #     'name': force_text(obj._meta.verbose_name),
        #     'object': force_text(obj)
        # }
        # add_comment(message)
        add_comment({
            'action': 'delete',
            'object_name': force_text(obj._meta.verbose_name),
            'object_repr': force_text(obj),
            'content_type': ContentType.objects.get_for_model(obj),
            'object_id': obj.id,
        })


class ModelProxy(object):
    def __init__(self, version):
        self._version = version
        self._object = version._object_version.object
        self._m2m_data = version._object_version.m2m_data
        self._cache = {}

    def __getattr__(self, item):
        obj = self._object
        try:
            f = obj._meta.get_field(item)
        except FieldDoesNotExist:
            f = None
        # print('-' * 10)
        # print(item, ':', f)
        if f:
            # print('one_to_one: ', f.one_to_one)
            # print('many_to_many: ', f.many_to_many)
            # print('related_model: ', f.related_model)

            if item in self._cache:
                return self._cache[item]
            if f.one_to_one:
                ct = ContentType.objects.get_for_model(f.related_model)
                related_obj = self._version.revision.version_set.filter(content_type=ct).first()
                if related_obj:
                    val = related_obj.object_version.object
                    self._cache[item] = val
                    return val
                self._cache[item] = None
                return None
            elif f.one_to_many:
                ct = ContentType.objects.get_for_model(f.related_model)
                res = []
                for related_obj in self._version.revision.version_set.filter(content_type=ct):
                    val = related_obj._object_version.object
                    res.append(val)
                self._cache[item] = res
                return res if res else None
            elif f.many_to_many:
                m2m_d = self._m2m_data
                if m2m_d and item in m2m_d:
                    val = list(f.related_model.objects.filter(id__in=m2m_d[item]))
                    self._cache[item] = val
                    return val
                self._cache[item] = None
                return None
        val = getattr(obj, item)
        return val

    def save(self, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, *args, **kwargs):
        raise NotImplementedError()
