import json
import logging

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy

from poms.common.models import OwnerModel, TimeStampedModel
from poms.configuration.utils import replace_special_chars_and_spaces

_l = logging.getLogger("poms.configuration")


class ConfigurationModel(OwnerModel):
    """
    just a good remainder to find entity by configuration_code
    """

    configuration_code = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy("Configuration Code"),
    )
    # TODO someday make it unique=True,
    user_code = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        verbose_name=gettext_lazy("User Code"),
    )

    class Meta:
        abstract = True

    # That is because we still need unique value e.g.
    #     - com.finmars.hnwi:buy_sell
    #     - com.finmars.asset_manager:buy_sell
    #
    #     frn:finmars:backend:::transactions.transactiontype:local.poms.space0000:*
    #     frn:finmars:backend:::transactions.transactiontype:com.finmars.hnwi:*
    #
    #     in that case con.finmars.hnwi already a user_code
    #     and :* is user_code qualifier

    def save(self, *args, **kwargs):
        # _l.info('self.configuration_code %s' % self.configuration_code)
        # _l.info('self.user_code %s' % self.user_code)

        if not self.configuration_code and hasattr(self, "master_user"):
            # Now new prefix is local.poms.[space_code] e.g. local.poms.space00000
            self.configuration_code = f"local.poms.{self.master_user.space_code}"

        if not self.user_code:
            raise RuntimeError("user_code is required")

        if self.configuration_code not in self.user_code:
            self.user_code = replace_special_chars_and_spaces(self.user_code).lower()
            self.user_code = f"{str(self.configuration_code)}:{str(self.user_code)}"

        super().save(*args, **kwargs)


CHANNEL_CHOICES = [
    ["stable", "Stable"],
    ["rc", "Release Candidate"],
]


class Configuration(TimeStampedModel):
    # com.finmars.hnwi
    configuration_code = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=gettext_lazy("configuration code"),
    )
    # High New Worth Individual
    name = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy("name"),
    )
    short_name = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy("short name"),
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy("notes"),
    )
    version = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy("version"),
    )
    type = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy("type"),
        default="general",
        help_text="Type of the configuration e.g general, pricing, ui, workflow, app",
    )
    channel = models.CharField(
        max_length=255,
        choices=CHANNEL_CHOICES,
        default="stable",
    )
    is_from_marketplace = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy("is from marketplace"),
    )
    is_package = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy("is package"),
    )
    manifest_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy("manifest_data"),
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name=gettext_lazy("is primary"),
    )

    class Meta:
        get_latest_by = "modified_at"
        ordering = [
            "created_at",
        ]

    def save(self, *args, **kwargs):
        if self.is_primary:
            qs = Configuration.objects.filter(is_primary=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            qs.update(is_primary=False)

        super().save(*args, **kwargs)

    @property
    def manifest(self):
        return None if self.manifest_data is None else self.manifest_data

    @manifest.setter
    def manifest(self, value):
        if value is None:
            self.manifest_data = None
        else:
            # if you still want to indent/sort, you can dump then load
            text = json.dumps(value, cls=DjangoJSONEncoder, sort_keys=True, indent=1)
            self.manifest_data = json.loads(text)


    def __str__(self):
        return f"{self.configuration_code} ({self.version})"


class NewMemberSetupConfiguration(ConfigurationModel):
    user_code = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        verbose_name=gettext_lazy("user code"),
        help_text=gettext_lazy(
            "Unique Code for this object. Used in Configuration and Permissions Logic"
        ),
    )
    name = models.CharField(
        max_length=255,
        verbose_name=gettext_lazy("name"),
        help_text="Human Readable Name of the object",
    )
    short_name = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy("short name"),
        help_text="Short Name of the object. Used in dropdown menus",
    )
    public_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=gettext_lazy("public name"),
        help_text=gettext_lazy("Used if user does not have permissions to view object"),
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name=gettext_lazy("notes"),
        help_text="Notes, any useful information about the object",
    )

    # Either provide configuration_code with version or upload zip
    target_configuration_code = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    target_configuration_version = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    target_configuration_channel = models.CharField(
        max_length=255,
        choices=CHANNEL_CHOICES,
        default="stable",
    )
    target_configuration_is_package = models.BooleanField(
        default=False,
    )
    file_url = models.TextField(
        blank=True,
        default="",
        verbose_name=gettext_lazy("File URL"),
    )
    file_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
