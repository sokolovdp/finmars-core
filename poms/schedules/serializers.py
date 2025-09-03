import logging

from rest_framework import serializers
from rest_framework.fields import empty

from poms.common.fields import DateTimeTzAwareField
from poms.common.serializers import ModelMetaSerializer
from poms.schedules.models import Schedule, ScheduleProcedure
from poms.users.fields import HiddenMemberField, MasterUserField

_l = logging.getLogger("poms.schedules")


class ScheduleProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleProcedure
        fields = [
            "type",
            "user_code",
            "order",
        ]


class RunScheduleSerializer(serializers.Serializer):
    schedules = serializers.CharField(allow_blank=False)

    def __init__(self, **kwargs):
        kwargs["context"] = context = kwargs.get("context", {}) or {}
        super().__init__(**kwargs)
        context["instance"] = self.instance


class ScheduleSerializer(ModelMetaSerializer):
    master_user = MasterUserField()
    owner = HiddenMemberField()
    last_run_at = DateTimeTzAwareField(read_only=True)
    next_run_at = DateTimeTzAwareField(read_only=True)
    procedures = ScheduleProcedureSerializer(required=False, many=True)
    data = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "master_user",
            "name",
            "user_code",
            "notes",
            "is_enabled",
            "cron_expr",
            "procedures",
            "last_run_at",
            "next_run_at",
            "error_handler",
            "data",
            "configuration_code",
            "owner",
        ]
        read_only_fields = ["last_run_at", "next_run_at"]

    def create(self, validated_data):
        _l.debug(f"create validated_data {validated_data}")

        procedures = validated_data.pop("procedures", empty)
        instance = super().create(validated_data)

        if procedures is not empty:
            self.save_procedures(instance, procedures)

        return instance

    def update(self, instance, validated_data):
        _l.debug(f"update instance {instance} validated_data {validated_data}")

        procedures = validated_data.pop("procedures", empty)
        instance = super().update(instance, validated_data)

        if procedures is not empty:
            procedures = self.save_procedures(instance, procedures)

        if procedures is not empty:
            instance.procedures.exclude(id__in=[proc.id for proc in procedures]).delete()

        return instance

    def save_procedures(self, instance, procedures_data):
        _l.debug(f"procedures_data {procedures_data}")

        current_procedures = {i.id: i for i in instance.procedures.all()}
        new_procedures = []
        for order, procedure_data in enumerate(procedures_data):  # noqa: B007
            pk = procedure_data.pop("id", None)
            procedure = current_procedures.pop(pk, None)

            _l.debug(f"procedure {procedure}")

            if procedure is None:
                try:
                    procedure = ScheduleProcedure.objects.get(schedule=instance, order=procedure_data["order"])
                except ScheduleProcedure.DoesNotExist:
                    procedure = ScheduleProcedure(schedule=instance)

            for attr, value in procedure_data.items():
                setattr(procedure, attr, value)

            procedure.save()
            new_procedures.append(procedure)

        return new_procedures
