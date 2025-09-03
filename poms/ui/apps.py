from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS, IntegrityError, ProgrammingError
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy


class UiConfig(AppConfig):
    name = "poms.ui"
    verbose_name = gettext_lazy("UI layout")

    def ready(self):
        post_migrate.connect(self.update_transaction_classes, sender=self)

    def update_transaction_classes(self, app_config, verbosity=2, using=DEFAULT_DB_ALIAS, **kwargs):
        from .models import PortalInterfaceAccessModel

        try:
            exists = set(PortalInterfaceAccessModel.objects.using(using).values_list("user_code", flat=True))
        except ProgrammingError as e:
            print(f"ProgrammingError {repr(e)}")
            return

        for id, value, code, name in PortalInterfaceAccessModel.CLASSES:
            if code not in exists:
                try:
                    PortalInterfaceAccessModel.objects.using(using).create(
                        id=id, user_code=code, name=name, description=name, value=value
                    )
                except (IntegrityError, ProgrammingError) as e:
                    print(f"Error {repr(e)}")

            else:
                obj = PortalInterfaceAccessModel.objects.using(using).get(user_code=code)
                obj.value = value
                if not obj.name:
                    obj.name = name
                if not obj.description:
                    obj.description = name
                obj.save()
