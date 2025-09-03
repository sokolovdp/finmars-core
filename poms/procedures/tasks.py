import logging
import traceback
from datetime import timedelta

import requests
from django.conf import settings
from django.utils.timezone import now

from poms.celery_tasks import finmars_task
from poms.common.models import ProxyRequest, ProxyUser
from poms.procedures.models import RequestDataFileProcedureInstance
from poms.system_messages.handlers import send_system_message
from poms.users.models import MasterUser

_l = logging.getLogger("poms.procedures")


@finmars_task(name="procedures.execute_data_procedure", bind=True)
def execute_data_procedure(
    self,
    procedure_instance_id,
    date_from=None,
    date_to=None,
    options=None,
    *args,
    **kwargs,
):
    from poms.procedures.handlers import DataProcedureProcess

    procedure_instance = RequestDataFileProcedureInstance.objects.get(pk=procedure_instance_id)

    master_user = procedure_instance.master_user
    procedure = procedure_instance.procedure
    member = procedure_instance.member

    instance = DataProcedureProcess(
        procedure=procedure,
        master_user=master_user,
        member=member,
        procedure_instance=procedure_instance,
    )

    if date_from:
        instance.update_procedure_date_from(date_from)
    if date_to:
        instance.update_procedure_date_to(date_to)

    if options:
        instance.update_procedure_options(options)

    instance.process()

    text = f"Data File Procedure {procedure.name}. Start processing"

    send_system_message(master_user=master_user, performed_by="System", description=text)


@finmars_task(name="procedures.procedure_request_data_file", bind=True, ignore_result=True)
def procedure_request_data_file(
    self,
    master_user,
    procedure_instance,
    transaction_file_result,
    data,
    *args,
    **kwargs,
):
    _l.debug("procedure_request_data_file processing")
    _l.debug("procedure_request_data_file procedure %s", procedure_instance)
    _l.debug("procedure_request_data_file transaction_file_result %s", transaction_file_result)
    _l.debug("procedure_request_data_file data %s", data)

    try:
        url = settings.DATA_FILE_SERVICE_URL + "/" + procedure_instance.procedure.provider.user_code + "/getfile"

        headers = {"Content-type": "application/json", "Accept": "application/json"}

        response = None

        _l.debug("url %s", url)

        procedure_instance.request_data = data

        try:
            response = requests.post(url=url, json=data, headers=headers, verify=settings.VERIFY_SSL)
        except requests.exceptions.ReadTimeout:
            _l.debug("Will not wait response")
            return
        _l.debug("response %s", response)
        _l.debug("response text %s", response.text)

        if response.status_code == 200:
            procedure_instance.save()

            data = response.json()

            if "error_message" in data:
                if data["error_message"]:
                    text = (
                        f"Data File Procedure {procedure_instance.procedure.user_code}. Error during request to "
                        f"Data Service. Error Message: {data['error_message']}"
                    )

                    send_system_message(
                        master_user=master_user,
                        performed_by="System",
                        type="error",
                        description=text,
                    )

                    procedure_instance.status = RequestDataFileProcedureInstance.STATUS_ERROR
                    procedure_instance.save()

        else:
            text = (
                f"Data File Procedure {procedure_instance.procedure.user_code}. Error during request to Data Service"
            )

            send_system_message(
                master_user=master_user,
                performed_by="System",
                type="error",
                description=text,
            )

            procedure_instance.status = RequestDataFileProcedureInstance.STATUS_ERROR
            procedure_instance.save()

        _l.debug("procedure instance saved %s", procedure_instance)

    except Exception as e:
        _l.debug("Can't send request to Data File Service. Is Transaction File Service offline?")
        _l.debug("Error %s", e)

        text = f"Data File Procedure {procedure_instance.procedure.user_code}. Data Service is offline"

        send_system_message(
            master_user=master_user,
            performed_by="System",
            type="error",
            description=text,
        )

        procedure_instance.status = RequestDataFileProcedureInstance.STATUS_ERROR
        procedure_instance.save()

        raise Exception("Data File Service is unavailable") from e


@finmars_task(name="procedures.run_data_procedure_from_formula", bind=True)
def run_data_procedure_from_formula(self, master_user_id, member_id, user_code, user_context, *args, **kwargs):
    _l.info("run_data_procedure_from_formula init")

    from poms.procedures.models import RequestDataFileProcedure
    from poms.users.models import MasterUser, Member

    master_user = MasterUser.objects.get(id=master_user_id)

    member = Member.objects.get(id=member_id)

    proxy_user = ProxyUser(member, master_user)
    proxy_request = ProxyRequest(proxy_user)

    context = {"request": proxy_request}

    merged_context = {}
    merged_context.update(context)

    if user_context:
        if "names" not in merged_context:
            merged_context["names"] = {}

        merged_context["names"].update(user_context)

    procedure = RequestDataFileProcedure.objects.get(master_user=master_user, user_code=user_code)

    kwargs.pop("user_context", None)

    from poms.procedures.handlers import DataProcedureProcess

    instance = DataProcedureProcess(
        procedure=procedure,
        master_user=master_user,
        member=member,
        context=merged_context,
        **kwargs,
    )
    instance.process()


# TODO Refactor to task_id
@finmars_task(name="procedures.remove_old_data_procedures")
def remove_old_data_procedures(*args, **kwargs):
    try:
        tasks = RequestDataFileProcedureInstance.objects.filter(created_at__lte=now() - timedelta(days=30))

        count = tasks.count()

        _l.info("Delete %s data procedures", count)
        master_user = MasterUser.objects.all().first()
        tasks.delete()

        send_system_message(
            master_user=master_user,
            type="info",
            title="Old Data Procedures Clearance",
            description=f"Finmars removed {count} tasks",
        )

    except Exception as e:
        master_user = MasterUser.objects.all().first()

        send_system_message(
            master_user=master_user,
            action_status="required",
            type="warning",
            title="Could not delete old Data Procedures",
            description=str(e),
        )

        _l.error("remove_old_data_procedures.exception %s", e)
        _l.error("remove_old_data_procedures.exception %s", traceback.format_exc())
