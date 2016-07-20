from __future__ import unicode_literals

import json
import logging
from threading import local

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.utils.decorators import ContextDecorator
from django.utils.encoding import force_text
from reversion import revisions as reversion
from reversion.errors import RevisionManagementError

_l = logging.getLogger('poms.audit')

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
        changes = reversion.get_comment()
        if changes:
            try:
                changes = json.loads(changes)
            except ValueError:
                changes = []
        else:
            changes = []
        ctype = message['content_type']
        message['content_type'] = '%s.%s' % (ctype.app_label, ctype.model)
        changes.append(message)
        set_comment(changes)
        # reversion.set_comment(json.dumps(comment))
        # _l.debug('> %s', audit_get_comment(reversion.get_comment()))
    except RevisionManagementError:
        pass


def set_comment(changes):
    reversion.set_comment(json.dumps(changes))


def get_comment():
    comment = reversion.get_comment()
    if comment:
        try:
            return json.loads(comment)
        except ValueError:
            pass
    return {}


def object_added(obj):
    if not is_active():
        return
    add_comment({
        'action': 'add',
        'object_name': force_text(obj._meta.verbose_name),
        'object_repr': force_text(obj),
        'content_type': ContentType.objects.get_for_model(obj),
        'object_id': obj.id,
    })


def object_changed(obj, fields):
    if not is_active():
        return
    add_comment({
        'action': 'change',
        'object_name': force_text(obj._meta.verbose_name),
        'object_repr': force_text(obj),
        'fields': fields,
        'content_type': ContentType.objects.get_for_model(obj),
        'object_id': obj.id,
    })


def object_changed_get_field(obj, name):
    if not is_active():
        return

    ctype = ContentType.objects.get_for_model(obj)
    content_type = '%s.%s' % (ctype.app_label, ctype.model)

    obj_change = None
    for o in get_comment():
        if o['object_id'] == obj.id and (o['content_type'] == content_type):
            obj_change = o

    if obj_change is not None:
        for f in obj_change.get('fields', []):
            if f['name'] == name:
                return f
    return None


def object_changed_update_field(obj, field):
    if not is_active():
        return

    ctype = ContentType.objects.get_for_model(obj)
    content_type = '%s.%s' % (ctype.app_label, ctype.model)

    obj_change = None

    changes = []
    for o in get_comment():
        if o['object_id'] == obj.id and (o['content_type'] == content_type):
            obj_change = o
        else:
            changes.append(o)

    obj_fields = []
    if obj_change is not None:
        for f in obj_change.get('fields', []):
            if f['name'] == field['name']:
                continue
            else:
                obj_fields.append(f)
    obj_fields.append(field)

    set_comment(changes)
    object_changed(obj, obj_fields)


def object_deleted(obj):
    if not is_active():
        return
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
