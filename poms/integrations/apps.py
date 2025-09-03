from django.apps import AppConfig
from django.db import DEFAULT_DB_ALIAS
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy


class IntegrationsConfig(AppConfig):
    name = "poms.integrations"
    verbose_name = gettext_lazy("Integrations")

    def ready(self):
        post_migrate.connect(self.update_transaction_classes, sender=self)
        post_migrate.connect(self.update_data_providers, sender=self)

        # noinspection PyUnresolvedReferences
        # import poms.integrations.handlers

    def update_transaction_classes(self, app_config, verbosity=2, using=DEFAULT_DB_ALIAS, **kwargs):
        from poms.common.utils import db_class_check_data

        from .models import (
            AccrualScheduleDownloadMethod,
            FactorScheduleDownloadMethod,
            ProviderClass,
        )

        # if not isinstance(app_config, IntegrationsConfig):
        #     return

        db_class_check_data(ProviderClass, verbosity, using)
        db_class_check_data(FactorScheduleDownloadMethod, verbosity, using)
        db_class_check_data(AccrualScheduleDownloadMethod, verbosity, using)

    def update_data_providers(self, app_config, verbosity=2, using=DEFAULT_DB_ALIAS, **kwargs):
        from .models import DataProvider

        provider_types = [
            {
                "id": 1,
                "name": "CIM bank",
                "user_code": "cim_bank",
            },
            {
                "id": 2,
                "name": "Julius Baer",
                "user_code": "julius_baer",
            },
            {
                "id": 3,
                "name": "Lombard Odier",
                "user_code": "lombard_odier",
            },
            {
                "id": 4,
                "name": "Revolut",
                "user_code": "revolut",
            },
            {
                "id": 5,
                "name": "Email Provider",
                "user_code": "email_provider",
            },
            {
                "id": 6,
                "name": "Universal Provider",
                "user_code": "universal",
            },
        ]

        providers_exists = DataProvider.objects.using(using).values_list("pk", flat=True)

        for type_ in provider_types:
            if type_["id"] in providers_exists:
                item = DataProvider.objects.using(using).get(id=type_["id"])

                item.name = type_["name"]
                item.user_code = type_["user_code"]

                item.save()

            else:
                DataProvider.objects.using(using).create(**type_)
