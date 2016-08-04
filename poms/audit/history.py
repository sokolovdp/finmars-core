from __future__ import unicode_literals

import json
import logging
from threading import local

import six
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import FieldDoesNotExist
from django.db.models.signals import post_init, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils.decorators import ContextDecorator
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _

from poms.common.middleware import get_request

_l = logging.getLogger('poms.audit')

_state = local()

_history_model_list = None


def get_history_model_list():
    global _history_model_list
    if _history_model_list is None:
        from poms.accounts.models import Account, AccountType, AccountAttributeType
        from poms.chats.models import ThreadGroup, Thread, Message, DirectMessage
        from poms.counterparties.models import Counterparty, CounterpartyAttributeType, Responsible, \
            ResponsibleAttributeType
        from poms.currencies.models import Currency, CurrencyHistory
        from poms.instruments.models import Instrument, InstrumentType, InstrumentAttributeType, PriceHistory
        from poms.portfolios.models import Portfolio, PortfolioAttributeType
        from poms.strategies.models import Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, \
            Strategy2Subgroup, Strategy2, Strategy3Group, Strategy3Subgroup, Strategy3
        from poms.transactions.models import TransactionType, Transaction, TransactionAttributeType
        from poms.users.models import MasterUser, Member
        from poms.integrations.models import InstrumentMapping

        _history_model_list = (
            AccountType, Account, AccountAttributeType,
            ThreadGroup, Thread, Message, DirectMessage,
            Counterparty, CounterpartyAttributeType, Responsible, ResponsibleAttributeType,
            Currency, CurrencyHistory,
            InstrumentType, Instrument, InstrumentAttributeType, PriceHistory,
            Portfolio, PortfolioAttributeType,
            Strategy1Group, Strategy1Subgroup, Strategy1, Strategy2Group, Strategy2Subgroup, Strategy2, Strategy3Group,
            Strategy3Subgroup, Strategy3,
            TransactionType, Transaction, TransactionAttributeType,
            MasterUser, Member,
            InstrumentMapping,
        )
    return _history_model_list


def activate():
    from poms.audit.models import ObjectHistoryEntry

    _state.active = True
    _state.added = []
    _state.changed = []
    _state.deleted = []
    _state.flag = ObjectHistoryEntry.DELETION
    _state.content_object = None
    _state.content_type = None
    _state.object_id = None


def deactivate():
    from poms.audit.models import ObjectHistoryEntry

    if getattr(_state, "active", True) and (_state.added or _state.changed or _state.deleted):
        if isinstance(_state.content_object, get_history_model_list()):
            request = get_request()
            content_object = _state.content_object
            message = json.dumps({
                'added': _state.added,
                'changed': _state.changed,
                'deleted': _state.deleted,
            }, sort_keys=True)
            ObjectHistoryEntry.objects.create(
                master_user=request.user.master_user,
                member=request.user.member,
                action_flag=_state.flag,
                message=message,
                # content_object=content_object,
                content_type=_state.content_type,
                object_id=_state.object_id
            )

    if hasattr(_state, "active"):
        del _state.active
    if hasattr(_state, "added"):
        del _state.added
    if hasattr(_state, "changed"):
        del _state.changed
    if hasattr(_state, "deleted"):
        del _state.deleted
    if hasattr(_state, "flag"):
        del _state.flag
    if hasattr(_state, "content_object"):
        del _state.content_object
    if hasattr(_state, "content_type"):
        del _state.content_type
    if hasattr(_state, "object_id"):
        del _state.object_id


def is_active():
    return getattr(_state, "active", False)


def set_content_object(content_object):
    _state.content_object = content_object
    _state.content_type = ContentType.objects.get_for_model(content_object)
    _state.object_id = content_object.id


def set_flag_addition():
    from poms.audit.models import ObjectHistoryEntry

    _state.flag = ObjectHistoryEntry.ADDITION


def set_flag_change():
    from poms.audit.models import ObjectHistoryEntry

    _state.flag = ObjectHistoryEntry.CHANGE


def set_flag_deletion():
    from poms.audit.models import ObjectHistoryEntry

    _state.flag = ObjectHistoryEntry.DELETION


class enable(ContextDecorator):
    def __enter__(self):
        activate()

    def __exit__(self, exc_type, exc_value, traceback):
        deactivate()


# def is_historical_proxy(obj):
#     return isinstance(obj, ModelProxy)


def register(model, **kwargs):
    # reversion.register(model, **kwargs)
    pass


# def _reversion_set_comment():
#     # if not is_active():
#     #     return
#     #
#     # changes = {
#     #     'added': _state.added,
#     #     'changed': _state.changed,
#     #     'deleted': _state.deleted,
#     # }
#     # # print('changes', '-' * 70)
#     # # pprint.pprint(changes)
#     # reversion.set_comment(json.dumps(changes))
#     pass


# def add_comment(message):
#     # try:
#     #     comment = reversion.get_comment()
#     #     if comment:
#     #         comment += ' ' + message
#     #     else:
#     #         comment = message
#     #     reversion.set_comment(comment)
#     # except RevisionManagementError:
#     #     pass
#     try:
#         changes = reversion.get_comment()
#         if changes:
#             try:
#                 changes = json.loads(changes)
#             except ValueError:
#                 changes = []
#         else:
#             changes = []
#         ctype = message['content_type']
#         message['content_type'] = '%s.%s' % (ctype.app_label, ctype.model)
#         changes.append(message)
#         set_comment(changes)
#         # reversion.set_comment(json.dumps(comment))
#         # _l.debug('> %s', audit_get_comment(reversion.get_comment()))
#     except RevisionManagementError:
#         pass
#
#
# def set_comment(changes):
#     reversion.set_comment(json.dumps(changes))
#
#
# def get_comment():
#     comment = reversion.get_comment()
#     if comment:
#         try:
#             return json.loads(comment)
#         except ValueError:
#             pass
#     return {}
#
#
# def object_added(obj):
#     if not is_active():
#         return
#     add_comment({
#         'action': 'add',
#         'object_name': force_text(obj._meta.verbose_name),
#         'object_repr': force_text(obj),
#         'content_type': ContentType.objects.get_for_model(obj),
#         'object_id': obj.id,
#     })
#
#
# def object_changed(obj, fields):
#     if not is_active():
#         return
#     add_comment({
#         'action': 'change',
#         'object_name': force_text(obj._meta.verbose_name),
#         'object_repr': force_text(obj),
#         'fields': fields,
#         'content_type': ContentType.objects.get_for_model(obj),
#         'object_id': obj.id,
#     })
#
#
# def object_changed_get_field(obj, name):
#     if not is_active():
#         return
#
#     ctype = ContentType.objects.get_for_model(obj)
#     content_type = '%s.%s' % (ctype.app_label, ctype.model)
#
#     obj_change = None
#     for o in get_comment():
#         if o['object_id'] == obj.id and (o['content_type'] == content_type):
#             obj_change = o
#
#     if obj_change is not None:
#         for f in obj_change.get('fields', []):
#             if f['name'] == name:
#                 return f
#     return None
#
#
# def object_changed_update_field(obj, field):
#     if not is_active():
#         return
#
#     ctype = ContentType.objects.get_for_model(obj)
#     content_type = '%s.%s' % (ctype.app_label, ctype.model)
#
#     obj_change = None
#
#     changes = []
#     for o in get_comment():
#         if o['object_id'] == obj.id and (o['content_type'] == content_type):
#             obj_change = o
#         else:
#             changes.append(o)
#
#     obj_fields = []
#     if obj_change is not None:
#         for f in obj_change.get('fields', []):
#             if f['name'] == field['name']:
#                 continue
#             else:
#                 obj_fields.append(f)
#     obj_fields.append(field)
#
#     set_comment(changes)
#     object_changed(obj, obj_fields)
#
#
# def object_deleted(obj):
#     if not is_active():
#         return
#     add_comment({
#         'action': 'delete',
#         'object_name': force_text(obj._meta.verbose_name),
#         'object_repr': force_text(obj),
#         'content_type': ContentType.objects.get_for_model(obj),
#         'object_id': obj.id,
#     })


# class ModelProxy(object):
#     def __init__(self, version):
#         self._version = version
#         self._object = version._object_version.object
#         self._m2m_data = version._object_version.m2m_data
#         self._cache = {}
#
#     def __getattr__(self, item):
#         obj = self._object
#         try:
#             f = obj._meta.get_field(item)
#         except FieldDoesNotExist:
#             f = None
#         # print('-' * 10)
#         # print(item, ':', f)
#         if f:
#             # print('one_to_one: ', f.one_to_one)
#             # print('many_to_many: ', f.many_to_many)
#             # print('related_model: ', f.related_model)
#
#             if item in self._cache:
#                 return self._cache[item]
#             if f.one_to_one:
#                 ct = ContentType.objects.get_for_model(f.related_model)
#                 related_obj = self._version.revision.version_set.filter(content_type=ct).first()
#                 if related_obj:
#                     val = related_obj.object_version.object
#                     self._cache[item] = val
#                     return val
#                 self._cache[item] = None
#                 return None
#             elif f.one_to_many:
#                 ct = ContentType.objects.get_for_model(f.related_model)
#                 res = []
#                 for related_obj in self._version.revision.version_set.filter(content_type=ct):
#                     val = related_obj._object_version.object
#                     res.append(val)
#                 self._cache[item] = res
#                 return res if res else None
#             elif f.many_to_many:
#                 m2m_d = self._m2m_data
#                 if m2m_d and item in m2m_d:
#                     val = list(f.related_model.objects.filter(id__in=m2m_d[item]))
#                     self._cache[item] = val
#                     return val
#                 self._cache[item] = None
#                 return None
#         val = getattr(obj, item)
#         return val
#
#     def save(self, *args, **kwargs):
#         raise NotImplementedError()
#
#     def delete(self, *args, **kwargs):
#         raise NotImplementedError()


def _is_enabled(obj):
    # return is_active() and reversion.is_registered(obj)
    return is_active()


def _is_disabled(obj):
    return not _is_enabled(obj)


def _fields_to_set(fields):
    ret = set()
    for k, v in six.iteritems(fields):
        if isinstance(v, list):
            ret.add((k, tuple(v)))
        else:
            ret.add((k, v))
    return ret


def _serialize(obj):
    return serializers.serialize('python', [obj])[0]


def _get_model(content_type):
    app_label, model = content_type.split('.')
    return ContentType.objects.get_by_natural_key(app_label, model).model_class()


def _get_content_type(instance):
    content_type = ContentType.objects.get_for_model(instance)
    return '%s.%s' % (content_type.app_label, content_type.model)


def _check_value(value):
    if type(value) in six.string_types:
        return value
    elif type(value) in six.integer_types:
        return value
    elif type(value) in (list, tuple,):
        return [_check_value(v) for v in value]
    else:
        return force_text(value)


def _make_rel_value(model, pk):
    if pk is None:
        return None
    ctype = ContentType.objects.get_for_model(model)
    if isinstance(pk, (list, tuple, set)):
        ret = []
        for tpk in pk:
            obj = ctype.get_object_for_this_type(pk=tpk)
            ret.append({
                'value': obj.id,
                'display': force_text(obj),
            })
        return ret

    obj = ctype.get_object_for_this_type(pk=pk)
    return {
        'value': obj.id,
        'display': force_text(obj),
    }


def _make_value(value):
    value = _check_value(value)
    return {
        'value': value,
        'display': value,
    }


@receiver(post_init, dispatch_uid='poms_history_post_init')
def _instance_post_init(sender, instance=None, **kwargs):
    if _is_disabled(instance):
        return
    if instance.pk:
        instance._poms_history_initial_state = _serialize(instance)
    else:
        instance._poms_history_initial_state = {'pk': None, 'fields': {}}


@receiver(post_save, dispatch_uid='poms_history_post_save')
def _instance_post_save(sender, instance=None, created=None, **kwargs):
    if _is_disabled(instance):
        return
    if not hasattr(instance, '_poms_history_initial_state'):
        return

    _l.debug('post_save: sender=%s, instance=%s, created=%s, kwargs=%s',
             sender, instance, created, kwargs)

    if created:
        # object_added(instance)
        _state.added.append({
            'action': 'add',
            'content_type': _get_content_type(instance),
            'object_id': instance.id,
            'object_repr': force_text(instance),
        })
        # _reversion_set_comment()
    else:
        i = instance._poms_history_initial_state
        c = _serialize(instance)

        if c['pk'] == i['pk']:
            cfields = _fields_to_set(c['fields'])
            ifileds = _fields_to_set(i['fields'])
            changed = ifileds - cfields
            fields = []
            for attr, v in changed:
                f = instance._meta.get_field(attr)
                old_value = i['fields'].get(attr, None)
                new_value = c['fields'].get(attr, None)

                if f.one_to_one or f.one_to_many or f.many_to_one:
                    old_value = _make_rel_value(f.related_model, old_value)
                    new_value = _make_rel_value(f.related_model, new_value)
                elif f.many_to_many:
                    # processed in _instance_m2m_changed
                    continue
                else:
                    old_value = _make_value(old_value)
                    new_value = _make_value(new_value)

                fields.append({
                    'name': six.text_type(f.name),
                    'old_value': old_value,
                    'new_value': new_value,
                })

            # fields.sort()
            # object_changed(instance, fields)
            if fields:
                _state.changed.append({
                    'action': 'changed',
                    'content_type': _get_content_type(instance),
                    'object_id': instance.id,
                    'object_repr': force_text(instance),
                    'fields': fields
                })
                # _reversion_set_comment()


@receiver(m2m_changed, dispatch_uid='poms_history_m2m_changed')
def _instance_m2m_changed(sender, instance=None, action=None, reverse=None, model=None, pk_set=None, **kwargs):
    if _is_disabled(instance):
        return
    if not hasattr(instance, '_poms_history_initial_state'):
        return

    _l.debug('m2m_changed.%s: sender=%s, instance=%s, reverse=%s, model=%s, pk_set=%s, kwargs=%s',
             action, sender, instance, reverse, model, pk_set, kwargs)

    if action not in ['pre_remove', 'pre_add']:
        return

    attr = None
    attr_ctype = ContentType.objects.get_for_model(model)
    for f in instance._meta.get_fields():
        if f.many_to_many:
            if f.auto_created:
                if f.through == sender:
                    # f = ft
                    attr = f.related_name
                    break
            else:
                if f.rel.through == sender:
                    # f = ft
                    attr = f.name
                    break
    if attr is None:
        return

    if attr not in instance._poms_history_initial_state:
        instance._poms_history_initial_state[attr] = [o.pk for o in getattr(instance, attr).all()]
        # _l.info('\t %s - %s -> %s', attr, attr_ctype, instance._poms_history_initial_state[attr])

    instance_ctype = _get_content_type(instance)
    state = None

    for s in _state.changed:
        if s['content_type'] == instance_ctype and s['object_id'] == instance.id:
            state = s
            break

    if state is None:
        fields = []
        state = {
            'action': 'changed',
            'content_type': instance_ctype,
            'object_id': instance.id,
            'object_repr': force_text(instance),
            'fields': fields
        }
        _state.changed.append(state)
    else:
        fields = state['fields']

    field = None
    for f in fields:
        if f['name'] == attr:
            field = f
            break
    if field is None:
        value = _make_rel_value(model, instance._poms_history_initial_state[attr])
        field = {
            'name': attr,
            'old_value': value,
            'new_value': value.copy(),
        }
        fields.append(field)

    new_value = set(x['value'] for x in field['new_value'])
    if action == 'pre_remove':
        new_value = new_value.difference(pk_set)
    elif action == 'pre_add':
        new_value = new_value.union(pk_set)

    field['new_value'] = _make_rel_value(model, new_value)
    # _reversion_set_comment()


@receiver(post_delete, dispatch_uid='poms_history_on_delete')
def _instance_post_delete(sender, instance=None, **kwargs):
    if _is_disabled(instance):
        return
    # if not hasattr(instance, '_poms_history_initial_state'):
    #     return
    _l.debug('post_delete: sender=%s, instance=%s, kwargs=%s',
             sender, instance, kwargs)
    # object_deleted(instance)

    _state.deleted.append({
        'action': 'delete',
        'content_type': _get_content_type(instance),
        'object_id': instance.id,
        'object_repr': force_text(instance),
    })
    # _reversion_set_comment()


def _get_display_value(value):
    if value is None:
        return None
    elif isinstance(value, dict):
        try:
            return _get_display_value(value['display'])
        except KeyError:
            return _get_display_value(value.get('value', None))
    elif isinstance(value, (list, tuple, set,)):
        l = sorted([_get_display_value(v) for v in value])
        return '[%s]' % (', '.join(l))
    elif isinstance(value, six.string_types):
        return '"%s"' % value
    return value


def make_comment(changes):
    if not changes:
        return None
    if isinstance(changes, six.string_types) and changes.startswith('{'):
        try:
            data = json.loads(changes)
        except ValueError:
            return changes
    else:
        data = changes
    if not isinstance(data, dict):
        return changes

    added = data.get('added', [])
    changed = data.get('changed', [])
    deleted = data.get('deleted', [])

    messages = []
    for o in added:
        try:
            model = _get_model(o['content_type'])
            message = _('Added %(name)s "%(object)s".') % {
                'name': model._meta.verbose_name,
                'object': o['object_repr']
            }
            messages.append(message)
        except KeyError:
            pass

    for o in changed:
        try:
            model = _get_model(o['content_type'])
            for of in o['fields']:
                try:
                    f = model._meta.get_field(of['name'])
                    if f.is_relation:
                        f_verbose_name = f.related_model._meta.verbose_name_plural
                    else:
                        f_verbose_name = getattr(f, 'verbose_name', of['name'])
                    message = _(
                        'Changed %(field)s in %(name)s "%(object)s" from %(old_value)s to %(new_value)s.') % {
                                  'field': f_verbose_name,
                                  # 'field': of['name'],
                                  'name': model._meta.verbose_name,
                                  'object': o['object_repr'],
                                  'old_value': _get_display_value(of['old_value']),
                                  'new_value': _get_display_value(of['new_value']),
                              }
                    messages.append(message)
                except (KeyError, FieldDoesNotExist):
                    pass
        except KeyError:
            pass

    for o in deleted:
        try:
            model = _get_model(o['content_type'])
            message = _('Deleted %(name)s "%(object)s".') % {
                'name': model._meta.verbose_name,
                'object': o['object_repr']
            }
            messages.append(message)
        except KeyError:
            pass

    return ' '.join(messages)
