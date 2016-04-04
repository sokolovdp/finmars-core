
def register_model(model):
    from django.db import models
    from django.utils.translation import ugettext_lazy as _
    from poms.users.models import UserObjectPermissionBase, GroupObjectPermissionBase

    app_module = '%s.models' % model._meta.app_label

    u_name = '%sUserObjectPermission' % model._meta.object_name
    u_attrs = {
        '__module__': app_module,
        'content_object': models.ForeignKey(model),
        'Meta': type(str('Meta'), (), {
            'app_label': model._meta.app_label,
            'verbose_name': _('%(name)s - user permission') % {
                'name': model._meta.verbose_name_plural
            },
            'verbose_name_plural': _('%(name)s - user permissions') % {
                'name': model._meta.verbose_name_plural
            },
        })
    }
    u_perms = type(str(u_name), (UserObjectPermissionBase,), u_attrs)

    g_name = '%sGroupObjectPermission' % model._meta.object_name
    g_attrs = {
        '__module__': app_module,
        'content_object': models.ForeignKey(model),
        'Meta': type(str('Meta'), (), {
            'app_label': model._meta.app_label,
            'verbose_name': _('%(name)s - group permission') % {
                'name': model._meta.verbose_name_plural
            },
            'verbose_name_plural': _('%(name)s - group permissions') % {
                'name': model._meta.verbose_name_plural
            },
        })
    }
    g_perms = type(str(g_name), (GroupObjectPermissionBase,), g_attrs)
    return u_perms, g_perms


def register_admin(*args):
    from django.contrib import admin
    from poms.users.models import UserObjectPermissionBase, GroupObjectPermissionBase
    from poms.users.admin import UserObjectPermissionAdmin, GroupObjectPermissionAdmin

    for model in args:
        if issubclass(model, UserObjectPermissionBase):
            admin.site.register(model, UserObjectPermissionAdmin)
        elif issubclass(model, GroupObjectPermissionBase):
            admin.site.register(model, GroupObjectPermissionAdmin)
