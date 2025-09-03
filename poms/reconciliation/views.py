from celery.result import AsyncResult
from django.core.signing import TimestampSigner
from django_filters.rest_framework import FilterSet, ModelChoiceFilter
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from poms.celery_tasks.models import CeleryTask
from poms.common.filters import CharFilter
from poms.common.utils import datetime_now
from poms.common.views import AbstractAsyncViewSet, AbstractModelViewSet
from poms.reconciliation.models import (
    ReconciliationBankFileField,
    ReconciliationComplexTransactionField,
    ReconciliationNewBankFileField,
)
from poms.reconciliation.serializers import (
    ProcessBankFileForReconcileSerializer,
    ReconciliationBankFileFieldSerializer,
    ReconciliationComplexTransactionFieldSerializer,
    ReconciliationNewBankFileFieldSerializer,
)
from poms.reconciliation.tasks import process_bank_file_for_reconcile
from poms.users.filters import OwnerByMasterUserFilter


class ReconciliationComplexTransactionFieldFilterSet(FilterSet):
    reference_name = CharFilter()

    class Meta:
        model = ReconciliationComplexTransactionField
        fields = []


class ReconciliationComplexTransactionFieldViewSet(AbstractModelViewSet):
    queryset = ReconciliationComplexTransactionField.objects
    serializer_class = ReconciliationComplexTransactionFieldSerializer
    filter_class = ReconciliationComplexTransactionFieldFilterSet

    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class ReconciliationBankFileFieldFilterSet(FilterSet):
    reference_name = CharFilter()
    linked_complex_transaction_field = ModelChoiceFilter(queryset=ReconciliationComplexTransactionField.objects.all())

    class Meta:
        model = ReconciliationBankFileField
        fields = []


class ReconciliationBankFileFieldViewSet(AbstractModelViewSet):
    queryset = ReconciliationBankFileField.objects
    serializer_class = ReconciliationBankFileFieldSerializer

    filter_class = ReconciliationBankFileFieldFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class ReconciliationNewBankFileFieldFilterSet(FilterSet):
    reference_name = CharFilter()

    class Meta:
        model = ReconciliationNewBankFileField
        fields = []


class ReconciliationNewBankFileFieldViewSet(AbstractModelViewSet):
    queryset = ReconciliationNewBankFileField.objects
    serializer_class = ReconciliationNewBankFileFieldSerializer

    filter_class = ReconciliationNewBankFileFieldFilterSet
    filter_backends = AbstractModelViewSet.filter_backends + [
        OwnerByMasterUserFilter,
    ]


class ProcessBankFileForReconcileViewSet(AbstractAsyncViewSet):
    serializer_class = ProcessBankFileForReconcileSerializer

    celery_task = process_bank_file_for_reconcile

    def get_serializer_context(self):
        context = super(AbstractAsyncViewSet, self).get_serializer_context()
        context["show_object_permissions"] = False
        return context

    def create(self, request, *args, **kwargs):
        print("TASK: process_bank_file_for_reconcile")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        task_id = instance.task_id

        signer = TimestampSigner()

        if task_id:
            res = AsyncResult(signer.unsign(task_id))

            try:
                celery_task = CeleryTask.objects.get(master_user=request.user.master_user, task_id=task_id)
            except CeleryTask.DoesNotExist:
                celery_task = None
                print("Cant create Celery Task")

            print(f"celery_task {celery_task}")

            if res.ready():
                instance = res.result
                if celery_task:
                    celery_task.finished_at = datetime_now()

            elif res.result:
                if "processed_rows" in res.result:
                    instance.processed_rows = res.result["processed_rows"]
                if "total_rows" in res.result:
                    instance.total_rows = res.result["total_rows"]

                if celery_task:
                    celery_task.data = {
                        "total_rows": res.result["total_rows"],
                        "processed_rows": res.result["processed_rows"],
                        "scheme_name": res.result["scheme_name"],
                        "file_name": res.result["file_name"],
                    }

            if instance.master_user.id != request.user.master_user.id:
                raise PermissionDenied()

            instance.task_id = task_id
            instance.task_status = res.status
            if celery_task:
                celery_task.task_status = res.status
                celery_task.save()

        else:
            res = self.celery_task.apply_async(
                kwargs={
                    "instance": instance,
                    "context": {
                        "space_code": request.space_code,
                        "realm_code": request.realm_code,
                    },
                }
            )
            instance.task_id = signer.sign(f"{res.id}")

            celery_task = CeleryTask.objects.create(
                master_user=request.user.master_user,
                member=request.user.member,
                started_at=datetime_now(),
                task_type="process_bank_file_for_reconcile",
                celery_task_id=res.id,
            )

            celery_task.save()

            instance.task_status = res.status

        serializer = self.get_serializer(instance=instance, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
