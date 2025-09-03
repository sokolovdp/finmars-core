import json
import logging
from collections.abc import Iterable
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.core.files.base import ContentFile
from django.core.serializers import serialize
from django.db import transaction
from django.utils.timezone import now

from poms.celery_tasks import finmars_task
from poms.celery_tasks.models import CeleryTask
from poms.common.storage import get_storage
from poms.common.utils import str_to_date
from poms.history.models import HistoricalRecord
from poms.history.utils import (
    get_local_path,
    get_storage_path,
    save_to_local_file,
    save_to_remote_storage,
    vacuum_table,
)
from poms.users.models import MasterUser

log = f"history_{Path(__name__).stem}.clear_old_journal_records:"
_l = logging.getLogger("poms.history")

DATE_FORMAT = "%Y-%m-%d"
CHUNK_SIZE = 5000
DAYS_30 = 30


def zip_records_to_buffer(filename: str, records: Iterable) -> bytes:
    dict_list = [record.as_dict for record in records]

    str_buffer = StringIO()
    json.dump(dict_list, str_buffer, ensure_ascii=False)

    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"{filename}.json", str_buffer.getvalue())

    return zip_buffer.getvalue()


def delete_selected_records(records_to_delete: Iterable):
    ids = [record.id for record in records_to_delete]

    with transaction.atomic():
        records = HistoricalRecord.objects.filter(id__in=ids).select_for_update()
        records.delete()


@finmars_task(name="history_tasks.clear_old_journal_records")
def clear_old_journal_records(*args, **kwargs):
    """
    Remove historical records older than ttl days, and save them into a file
    """

    _l.info(f"{log} started...")

    master = MasterUser.objects.first()
    if not master:
        _l.error(f"{log} aborted, no master user")
        return

    ttl = MasterUser.JOURNAL_POLICY_DAYS.get(master.journal_storage_policy, DAYS_30)
    delete_time = now() - timedelta(days=ttl)
    date_from = delete_time.strftime(DATE_FORMAT)

    old_records = HistoricalRecord.objects.filter(
        created_at__lt=delete_time,
    ).order_by(
        "created_at",
    )

    total_count = old_records.count()

    _l.info(f"{log} {total_count} records to be deleted")
    if not old_records:
        _l.info(f"{log} aborted, nothing to delete")
        return

    start = 0
    chunk_no = 1
    while start < total_count:
        end = start + CHUNK_SIZE

        chunk = old_records[start:end]

        filename = f"deleted_records_from_{date_from}_chunk_{chunk_no}"

        buffer = zip_records_to_buffer(filename, chunk)
        _l.info(f"{log} created buffer of {len(buffer)} size")

        try:
            storage = get_storage()
            if storage:
                remote_path = get_storage_path(filename, master.space_code)
                save_to_remote_storage(storage, remote_path, buffer)
                _l.info(f"{log} deleted records saved to remote storage {remote_path}")
            else:
                local_path = get_local_path(filename)
                save_to_local_file(local_path, buffer)
                _l.info(f"{log} deleted records saved to local file {local_path}")

        except Exception as e:
            _l.error(f"{log} unable to save deleted records into file {filename} due to error: {repr(e)}")
            return

        try:
            delete_selected_records(old_records)
            vacuum_table(table=HistoricalRecord)

        except Exception as e:
            _l.error(f"{log} unable to delete records and vacuum the table: {repr(e)}")
            return

        else:
            _l.info(f"{log} {total_count} records successfully deleted from history")

        chunk_no += 1
        start = end


# Generate days range
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def main_export_journal_to_storage(space_code: str, single_date: datetime, storage) -> int:
    _l.info("single_date %s", single_date)
    year, month, day = single_date.year, single_date.month, single_date.day

    records = HistoricalRecord.objects.filter(created_at__date=single_date)

    _l.info("records count %s", records.count())

    if records.exists():
        data = serialize("json", records)
        json_file = ContentFile(data.encode("utf-8"))
        path = space_code + "/.system/journal"
        file_name = f"{path}/{year}/{month}/{day}.json"

        storage.save(file_name, json_file)

        records.delete()

        return records.count()

    return None


@finmars_task(name="history.export_journal_to_storage", bind=True)
def export_journal_to_storage(self, task_id, *args, **kwargs):
    """
    Export historical records to storage
    """

    task = CeleryTask.objects.get(id=task_id)
    task.celery_task_id = self.request.id
    task.status = CeleryTask.STATUS_PENDING
    task.save()

    try:
        date_from = str_to_date(task.options_object.get("date_from"))
    except Exception:
        if not (first_historical_record := HistoricalRecord.objects.order_by("created_at").first()):
            _l.info("No records found")
            return

    date_from = first_historical_record.created_at.date()
    date_to = str_to_date(task.options_object.get("date_to"))
    space_code = task.master_user.space_code

    storage = get_storage()

    total = HistoricalRecord.objects.filter(created_at__range=[date_from, date_to]).count()
    if not total:
        result_object = {
            "message": "No records found",
        }
        task.result_object = result_object
        task.status = CeleryTask.STATUS_DONE
        task.save()
        return

    count = 0

    # Iterate over each day in the range
    for single_date in daterange(date_from, date_to):
        export_count = main_export_journal_to_storage(space_code, single_date, storage)

        if export_count:
            count += export_count

            task.update_progress(
                {
                    "current": count,
                    "total": total,
                    "percent": round(count / (total / 100)),
                    "description": f"Going to export for {single_date}",
                }
            )

    result_object = {
        "message": f"Exported {count} records to storage",
    }
    task.result_object = result_object
    task.status = CeleryTask.STATUS_DONE
    task.save()


@finmars_task(name="history.common_export_journal_to_storage", bind=True)
def common_export_journal_to_storage(self, *args, **kwargs):
    days = kwargs.get("days", 90)
    context = kwargs.get("context")
    if not context:
        _l.info("No context found")
        return

    space_code = context.get("space_code")

    date_to = (datetime.now() - timedelta(days=days)).date()

    if not (first_historical_record := HistoricalRecord.objects.order_by("created_at").first()):
        _l.info("No records found")
        return

    date_from = first_historical_record.created_at.date()

    total = HistoricalRecord.objects.filter(created_at__range=[date_from, date_to]).count()
    if not total:
        _l.info("No records found")
        return

    count = 0
    storage = get_storage()

    for single_date in daterange(date_from, date_to):
        export_count = main_export_journal_to_storage(space_code, single_date, storage)

        if export_count:
            _l.info(f"Exported {export_count} records from {single_date}")
            count += export_count
            continue

        _l.info(f"No records found from {single_date}")
