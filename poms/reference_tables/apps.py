from django.apps import AppConfig
from django.utils.translation import gettext_lazy


class ReferenceTablesConfig(AppConfig):
    name = "poms.reference_tables"
    verbose_name = gettext_lazy("Reference Tables")
