from __future__ import unicode_literals

import logging
from threading import local

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.db.models.signals import post_init, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.utils.decorators import ContextDecorator

from poms.common.middleware import get_request

_l = logging.getLogger('poms.audit')

_state = local()


def _accept(model):
    from poms.common.models import AbstractClassModel
    from poms.integrations.models import Task

    app_label = getattr(model._meta, 'app_label', None)
    if app_label not in ['users', 'chats', 'tags', 'accounts', 'counterparties', 'currencies', 'instruments',
                         'integrations', 'portfolios', 'strategies', 'transactions', ]:
        return False
    if issubclass(model, (AbstractClassModel, Task)):
        return False
    return True


_history_model_list = None


def get_history_model_list():
    global _history_model_list
    if _history_model_list is None:
        _history_model_list = tuple(m for m in apps.get_models() if _accept(m))
    return _history_model_list


def activate():
    _state.active = True

    _state.flag = None
    set_flag_addition()

    _state.actor_content_object = None
    _state.actor_content_object_id = None
    _state.entries4 = []


def deactivate():
    if getattr(_state, "active", True) and _state.entries4:
        if _state.actor_content_object:
            group_id = 0
            actor_content_type = ContentType.objects.get_for_model(_state.actor_content_object)
            actor_object_id = _state.actor_content_object_id
            actor_object_repr = str(_state.actor_content_object)
            user = get_request().user

            for e in _state.entries4:
                e.master_user = user.master_user
                e.member = user.member
                e.group_id = group_id

                e.actor_content_type = actor_content_type
                e.actor_object_id = actor_object_id
                e.actor_object_repr = actor_object_repr

                e.save()

                if group_id == 0:
                    group_id = e.id
                    e.group_id = group_id
                    e.save(update_fields=['group_id'])
        else:
            _l.debug('actor_content_object is not defined (maybe registration)')

    if hasattr(_state, "active"):
        del _state.active
    if hasattr(_state, "flag"):
        del _state.flag
    if hasattr(_state, "actor_content_object"):
        del _state.actor_content_object
    if hasattr(_state, "actor_content_object_id"):
        del _state.actor_content_object_id
    if hasattr(_state, "entries4"):
        del _state.entries4


def is_active():
    return getattr(_state, "active", False)


def set_actor_content_object(obj):
    _state.actor_content_object = obj
    _state.actor_content_object_id = obj.id


def set_flag_addition():
    from poms.audit.models import ObjectHistory4Entry

    _state.flag = ObjectHistory4Entry.ADDITION


def set_flag_change():
    from poms.audit.models import ObjectHistory4Entry

    _state.flag = ObjectHistory4Entry.CHANGE


def set_flag_deletion():
    from poms.audit.models import ObjectHistory4Entry

    _state.flag = ObjectHistory4Entry.DELETION


class enable(ContextDecorator):
    def __enter__(self):
        activate()

    def __exit__(self, exc_type, exc_value, traceback):
        deactivate()


def _is_enabled(obj):
    from poms.audit.models import ObjectHistory4Entry

    if not is_active():
        return False
    if isinstance(obj, ObjectHistory4Entry):
        return False
    if isinstance(obj, get_history_model_list()):
        return True
    return False


def _is_disabled(obj):
    return not _is_enabled(obj)


def _fields_to_set(fields):
    ret = set()
    for k, v in fields.items():
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


# def _check_value(value):
#     if type(value) in six.string_types:
#         return value
#     elif type(value) in six.integer_types:
#         return value
#     elif type(value) in (list, tuple,):
#         return [_check_value(v) for v in value]
#     else:
#         return force_text(value)
#
#
# def _make_rel_value(model, pk):
#     if pk is None:
#         return None
#     ctype = ContentType.objects.get_for_model(model)
#     if isinstance(pk, (list, tuple, set)):
#         ret = []
#         for tpk in pk:
#             obj = ctype.get_object_for_this_type(pk=tpk)
#             ret.append({
#                 'value': obj.id,
#                 'display': force_text(obj),
#             })
#         return ret
#
#     obj = ctype.get_object_for_this_type(pk=pk)
#     return {
#         'value': obj.id,
#         'display': force_text(obj),
#     }
#
#
# def _make_value(value):
#     value = _check_value(value)
#     return {
#         'value': value,
#         'display': value,
#     }


def _value_to_str(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    else:
        return str(value)


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
    from poms.audit.models import ObjectHistory4Entry

    if _is_disabled(instance):
        return
    if not hasattr(instance, '_poms_history_initial_state'):
        return

    _l.debug('post_save: sender=%s, instance=%s, created=%s, kwargs=%s',
             sender, instance, created, kwargs)

    if created:
        # _state.added.append({
        #     'action': 'add',
        #     'content_type': _get_content_type(instance),
        #     'object_id': instance.id,
        #     'object_repr': force_text(instance),
        # })

        _state.entries4.append(ObjectHistory4Entry(
            action_flag=ObjectHistory4Entry.ADDITION,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            object_repr=str(instance)
        ))

    else:
        i = instance._poms_history_initial_state
        c = _serialize(instance)

        if c['pk'] == i['pk']:
            cfields = _fields_to_set(c['fields'])
            ifileds = _fields_to_set(i['fields'])
            changed = ifileds - cfields
            # fields = []
            for attr, v in changed:
                f = instance._meta.get_field(attr)
                old_value = i['fields'].get(attr, None)
                new_value = c['fields'].get(attr, None)

                _l.debug('post_save: changed field "%s": %s -> %s', f, old_value, new_value)

                e4 = ObjectHistory4Entry(
                    action_flag=ObjectHistory4Entry.CHANGE,
                    content_type=ContentType.objects.get_for_model(instance),
                    object_id=instance.id,
                    object_repr=str(instance),

                    field_name=str(f.name)
                )

                if f.one_to_one:
                    _l.warn('_instance_post_save: one_to_one')
                    pass
                elif f.one_to_many:
                    _l.warn('_instance_post_save: one_to_many')
                    pass
                elif f.many_to_one:
                    fctype = ContentType.objects.get_for_model(f.related_model)

                    if new_value:
                        e4.value_content_type = fctype
                        e4.value_object_id = new_value
                        e4.value = str(fctype.get_object_for_this_type(pk=new_value))

                    if old_value:
                        e4.old_value_content_type = fctype
                        e4.old_value_object_id = old_value
                        e4.old_value = str(fctype.get_object_for_this_type(pk=old_value))

                    _state.entries4.append(e4)
                elif f.many_to_many:
                    pass
                else:
                    e4.value = _value_to_str(new_value)
                    e4.old_value = _value_to_str(old_value)
                    _state.entries4.append(e4)

                    #     if f.one_to_one or f.one_to_many or f.many_to_one:
                    #         old_value = _make_rel_value(f.related_model, old_value)
                    #         new_value = _make_rel_value(f.related_model, new_value)
                    #     elif f.many_to_many:
                    #         # processed in _instance_m2m_changed
                    #         continue
                    #     else:
                    #         old_value = _make_value(old_value)
                    #         new_value = _make_value(new_value)
                    #
                    #     fields.append({
                    #         'name': str(f.name),
                    #         'old_value': old_value,
                    #         'new_value': new_value,
                    #     })
                    #
                    # if fields:
                    #     _state.changed.append({
                    #         'action': 'changed',
                    #         'content_type': _get_content_type(instance),
                    #         'object_id': instance.id,
                    #         'object_repr': force_text(instance),
                    #         'fields': fields
                    #     })
                    # _reversion_set_comment()


@receiver(m2m_changed, dispatch_uid='poms_history_m2m_changed')
def _instance_m2m_changed(sender, instance=None, action=None, reverse=None, model=None, pk_set=None, **kwargs):
    from poms.audit.models import ObjectHistory4Entry

    if _is_disabled(instance):
        return
    if not hasattr(instance, '_poms_history_initial_state'):
        return

    _l.debug('m2m_changed.%s: sender=%s, instance=%s, reverse=%s, model=%s, pk_set=%s, kwargs=%s',
             action, sender, instance, reverse, model, pk_set, kwargs)

    if _state.flag == ObjectHistory4Entry.ADDITION:
        return

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

    for pk in pk_set:
        e4 = ObjectHistory4Entry(
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.id,
            object_repr=str(instance),

            field_name=str(attr),
            value_content_type=attr_ctype,
            value_object_id=pk,
            value=str(attr_ctype.get_object_for_this_type(pk=pk))
        )

        if action == 'pre_add':
            e4.action_flag = ObjectHistory4Entry.M2M_ADDITION
            _state.entries4.append(e4)
        elif action == 'pre_remove':
            e4.action_flag = ObjectHistory4Entry.M2M_DELETION
            _state.entries4.append(e4)

            # instance_ctype = _get_content_type(instance)
            # state = None
            #
            # for s in _state.changed:
            #     if s['content_type'] == instance_ctype and s['object_id'] == instance.id:
            #         state = s
            #         break
            #
            # if state is None:
            #     fields = []
            #     state = {
            #         'action': 'changed',
            #         'content_type': instance_ctype,
            #         'object_id': instance.id,
            #         'object_repr': force_text(instance),
            #         'fields': fields
            #     }
            #     _state.changed.append(state)
            # else:
            #     fields = state['fields']
            #
            # field = None
            # for f in fields:
            #     if f['name'] == attr:
            #         field = f
            #         break
            # if field is None:
            #     value = _make_rel_value(model, instance._poms_history_initial_state[attr])
            #     field = {
            #         'name': attr,
            #         'old_value': value,
            #         'new_value': value.copy(),
            #     }
            #     fields.append(field)
            #
            # new_value = set(x['value'] for x in field['new_value'])
            # if action == 'pre_remove':
            #     new_value = new_value.difference(pk_set)
            # elif action == 'pre_add':
            #     new_value = new_value.union(pk_set)
            #
            # field['new_value'] = _make_rel_value(model, new_value)
            # # _reversion_set_comment()


@receiver(post_delete, dispatch_uid='poms_history_on_delete')
def _instance_post_delete(sender, instance=None, **kwargs):
    from poms.audit.models import ObjectHistory4Entry

    if _is_disabled(instance):
        return

    _l.debug('post_delete: sender=%s, instance=%s, kwargs=%s',
             sender, instance, kwargs)

    # _state.deleted.append({
    #     'action': 'delete',
    #     'content_type': _get_content_type(instance),
    #     'object_id': instance.id,
    #     'object_repr': force_text(instance),
    # })

    _state.entries4.append(ObjectHistory4Entry(
        action_flag=ObjectHistory4Entry.DELETION,
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id,
        object_repr=str(instance)
    ))

# def _get_display_value(value):
#     if value is None:
#         return None
#     elif isinstance(value, dict):
#         try:
#             return _get_display_value(value['display'])
#         except KeyError:
#             return _get_display_value(value.get('value', None))
#     elif isinstance(value, (list, tuple, set,)):
#         l = sorted([_get_display_value(v) for v in value])
#         return '[%s]' % (', '.join(l))
#     elif isinstance(value, six.string_types):
#         return '"%s"' % value
#     return value


# def make_comment(changes):
#     if not changes:
#         return None
#     if isinstance(changes, six.string_types) and changes.startswith('{'):
#         try:
#             data = json.loads(changes)
#         except ValueError:
#             return changes
#     else:
#         data = changes
#     if not isinstance(data, dict):
#         return changes
#
#     added = data.get('added', [])
#     changed = data.get('changed', [])
#     deleted = data.get('deleted', [])
#
#     messages = []
#     for o in added:
#         try:
#             model = _get_model(o['content_type'])
#             message = _('Added %(name)s "%(object)s".') % {
#                 'name': model._meta.verbose_name,
#                 'object': o['object_repr']
#             }
#             messages.append(message)
#         except KeyError:
#             pass
#
#     for o in changed:
#         try:
#             model = _get_model(o['content_type'])
#             for of in o['fields']:
#                 try:
#                     f = model._meta.get_field(of['name'])
#                     if f.is_relation:
#                         f_verbose_name = f.related_model._meta.verbose_name_plural
#                     else:
#                         f_verbose_name = getattr(f, 'verbose_name', of['name'])
#                     message = _(
#                         'Changed %(field)s in %(name)s "%(object)s" from %(old_value)s to %(new_value)s.') % {
#                                   'field': f_verbose_name,
#                                   # 'field': of['name'],
#                                   'name': model._meta.verbose_name,
#                                   'object': o['object_repr'],
#                                   'old_value': _get_display_value(of['old_value']),
#                                   'new_value': _get_display_value(of['new_value']),
#                               }
#                     messages.append(message)
#                 except (KeyError, FieldDoesNotExist):
#                     pass
#         except KeyError:
#             pass
#
#     for o in deleted:
#         try:
#             model = _get_model(o['content_type'])
#             message = _('Deleted %(name)s "%(object)s".') % {
#                 'name': model._meta.verbose_name,
#                 'object': o['object_repr']
#             }
#             messages.append(message)
#         except KeyError:
#             pass
#
#     return ' '.join(messages)
