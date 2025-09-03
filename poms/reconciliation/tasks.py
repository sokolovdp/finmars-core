import csv
import logging

# from poms.integrations.storage import import_file_storage
from tempfile import NamedTemporaryFile

from django.utils.translation import gettext_lazy

from poms.celery_tasks import finmars_task
from poms.common.storage import get_storage
from poms.common.utils import date_now
from poms.expressions_engine import formula
from poms.reconciliation.models import (
    ReconciliationBankFileField,
    ReconciliationNewBankFileField,
)
from poms.reconciliation.serializers import (
    ReconciliationBankFileFieldSerializer,
    ReconciliationNewBankFileFieldSerializer,
)

_l = logging.getLogger("poms.reconciliation")


storage = get_storage()


@finmars_task(name="reconciliation.process_bank_file_for_reconcile", bind=True)
def process_bank_file_for_reconcile(self, instance, *args, **kwargs):  # noqa: PLR0915
    _l.debug("complex_transaction_file_import: %s", instance)

    instance.processed_rows = 0

    scheme = instance.scheme
    scheme_inputs = list(scheme.inputs.all())

    recon_scenarios = list(scheme.recon_scenarios.all())

    _now = date_now()

    def _process_csv_file(file):  # noqa: PLR0912, PLR0915
        instance.processed_rows = 0

        delimiter = instance.delimiter.encode("utf-8").decode("unicode_escape")

        reader = csv.reader(
            file,
            delimiter=delimiter,
            quotechar=instance.quotechar,
            strict=False,
            skipinitialspace=True,
        )

        instance.results = []

        for row_index, row in enumerate(reader):
            _l.debug("process row: %s -> %s", row_index, row)
            if (row_index == 0 and instance.skip_first_line) or not row:
                _l.debug("skip first row")
                continue

            inputs_raw = {}
            inputs = {}
            inputs_error = []
            inputs_conversion_error = []

            error_rows = {
                "level": "info",
                "error_message": "",
                "original_row_index": row_index,
                "original_row": row,
                "error_data": {
                    "columns": {
                        "imported_columns": [],
                        "converted_imported_columns": [],
                        "transaction_type_selector": [],
                        "executed_input_expressions": [],
                    },
                    "data": {
                        "imported_columns": [],
                        "converted_imported_columns": [],
                        "transaction_type_selector": [],
                        "executed_input_expressions": [],
                    },
                },
                "error_reaction": "Success",
            }

            matched_selector = False

            for i in scheme_inputs:
                error_rows["error_data"]["columns"]["imported_columns"].append(i.name)

                try:
                    inputs_raw[i.name] = row[i.column - 1]
                    error_rows["error_data"]["data"]["imported_columns"].append(row[i.column - 1])
                except Exception:
                    _l.debug("can't process input: %s|%s", i.name, i.column, exc_info=True)
                    error_rows["error_data"]["data"]["imported_columns"].append(gettext_lazy("Invalid expression"))
                    inputs_error.append(i)

            if inputs_error:
                error_rows["level"] = "error"

                error_rows["error_message"] = error_rows["error_message"] + str(
                    gettext_lazy("Can't process fields: %(inputs)s")
                    % {"inputs": ", ".join("[" + i.name + "] (Can't find input)" for i in inputs_error)}
                )
                instance.error_rows.append(error_rows)
                if instance.break_on_error:
                    error_rows["error_reaction"] = "Break"
                    instance.error_row_index = row_index
                    instance.error_rows.append(error_rows)
                    return
                else:
                    error_rows["error_reaction"] = "Continue import"
                    continue

            for i in scheme_inputs:
                error_rows["error_data"]["columns"]["converted_imported_columns"].append(
                    i.name + ": Conversion Expression " + "(" + i.name_expr + ")"
                )

                try:
                    inputs[i.name] = formula.safe_eval(i.name_expr, names=inputs_raw)
                    error_rows["error_data"]["data"]["converted_imported_columns"].append(row[i.column - 1])
                except Exception:
                    _l.debug(
                        "can't process conversion input: %s|%s",
                        i.name,
                        i.column,
                        exc_info=True,
                    )
                    error_rows["error_data"]["data"]["converted_imported_columns"].append(
                        gettext_lazy("Invalid expression")
                    )
                    inputs_conversion_error.append(i)

            if inputs_conversion_error:
                error_rows["level"] = "error"

                error_rows["error_message"] = error_rows["error_message"] + str(
                    gettext_lazy("Can't process fields: %(inputs)s")
                    % {
                        "inputs": ", ".join(
                            "[" + i.name + '] (Imported column conversion expression, value; "' + i.name_exp + '")'
                            for i in inputs_conversion_error
                        )
                    }
                )
                instance.error_rows.append(error_rows)
                if instance.break_on_error:
                    error_rows["error_reaction"] = "Break"
                    instance.error_row_index = row_index
                    instance.error_rows.append(error_rows)
                    return
                else:
                    error_rows["error_reaction"] = "Continue import"
                    continue

            try:
                selector_value = formula.safe_eval(scheme.rule_expr, names=inputs)
            except Exception:
                error_rows["level"] = "error"

                _l.debug("can't process selector value expression", exc_info=True)
                error_rows["error_message"] = (
                    error_rows["error_message"] + "\n" + "\n" + str(gettext_lazy("Can't eval rule expression"))
                )
                instance.error_rows.append(error_rows)
                if instance.break_on_error:
                    instance.error_row_index = row_index
                    instance.error_rows.append(error_rows)
                    return
                else:
                    continue
            _l.debug("selector_value value: %s", selector_value)

            matched_selector = False
            processed_scenarios = 0

            for scheme_recon in recon_scenarios:
                matched_selector = False

                selector_values = scheme_recon.selector_values.all()

                for item in selector_values:
                    if item.value == selector_value:
                        matched_selector = True

                if matched_selector:
                    processed_scenarios = processed_scenarios + 1

                    result_row = {}

                    for i in scheme_inputs:
                        result_row[i.name] = row[i.column - 1]

                    result_row["fields"] = []

                    fields = {}  # noqa: F841
                    fields_error = []  # noqa: F841
                    for field in scheme_recon.fields.all():
                        new_bank_file_field = ReconciliationNewBankFileField(master_user=instance.master_user)

                        new_bank_file_field.reference_name = field.reference_name
                        new_bank_file_field.description = field.description
                        new_bank_file_field.file_name = instance.filename
                        new_bank_file_field.import_scheme_name = instance.scheme.scheme_name

                        try:
                            new_bank_file_field.source_id = formula.safe_eval(
                                scheme_recon.line_reference_id, names=inputs
                            )
                        except formula.InvalidExpression:
                            new_bank_file_field.value_string = "<InvalidExpression>"

                        try:
                            new_bank_file_field.reference_date = formula.safe_eval(
                                scheme_recon.reference_date, names=inputs
                            )
                        except formula.InvalidExpression:
                            new_bank_file_field.reference_date = _now

                        if field.value_string:
                            try:
                                new_bank_file_field.value_string = formula.safe_eval(field.value_string, names=inputs)
                            except formula.InvalidExpression:
                                new_bank_file_field.value_string = "<InvalidExpression>"
                        if field.value_float:
                            try:  # noqa: SIM105
                                new_bank_file_field.value_float = formula.safe_eval(field.value_float, names=inputs)
                            except formula.InvalidExpression:
                                pass

                        if field.value_date:
                            try:  # noqa: SIM105
                                new_bank_file_field.value_date = formula.safe_eval(field.value_date, names=inputs)
                            except formula.InvalidExpression:
                                pass

                        try:
                            existed_bank_file_field = ReconciliationBankFileField.objects.get(
                                master_user=instance.master_user,
                                source_id=new_bank_file_field.source_id,
                                reference_name=new_bank_file_field.reference_name,
                                import_scheme_name=new_bank_file_field.import_scheme_name,
                            )

                            serializer = ReconciliationBankFileFieldSerializer(existed_bank_file_field)

                        except ReconciliationBankFileField.DoesNotExist:
                            new_bank_file_field.save()

                            print(f"id {new_bank_file_field.id}")

                            serializer = ReconciliationNewBankFileFieldSerializer(new_bank_file_field)

                        result_row["fields"].append(serializer.data)

                        try:
                            result_row["source_id"] = formula.safe_eval(scheme_recon.line_reference_id, names=inputs)
                        except formula.InvalidExpression:
                            result_row["source_id"] = "<InvalidExpression>"

                    instance.processed_rows = instance.processed_rows + 1

                    self.update_state(
                        task_id=instance.task_id,
                        state=Task.STATUS_PENDING,  # noqa: F821
                        meta={
                            "processed_rows": instance.processed_rows,
                            "total_rows": instance.total_rows,
                            "scheme_name": instance.scheme.scheme_name,
                            "file_name": instance.filename,
                        },
                    )

                    instance.results.append(result_row)

            if processed_scenarios == 0:
                error_rows["level"] = "error"

                if instance.break_on_error:
                    instance.error_row_index = row_index
                    error_rows["error_reaction"] = "Break"
                    instance.error_rows.append(error_rows)
                    return
                else:
                    error_rows["error_reaction"] = "Continue import"

            instance.error_rows.append(error_rows)

    def _row_count(file):
        delimiter = instance.delimiter.encode("utf-8").decode("unicode_escape")

        reader = csv.reader(
            file,
            delimiter=delimiter,
            quotechar=instance.quotechar,
            strict=False,
            skipinitialspace=True,
        )

        row_index = 0

        for row_index, row in enumerate(reader):  # noqa: B007
            pass
        return row_index

    instance.error_rows = []
    try:
        with storage.open(instance.file_path, "rb") as f, NamedTemporaryFile() as tmpf:
            _l.debug("tmpf")
            _l.debug(tmpf)

            for chunk in f.chunks():
                tmpf.write(chunk)
            tmpf.flush()
            with open(tmpf.name, encoding=instance.encoding, errors="ignore") as cfr:
                instance.total_rows = _row_count(cfr)
                self.update_state(
                    task_id=instance.task_id,
                    state=Task.STATUS_PENDING,  # noqa: F821
                    meta={
                        "total_rows": instance.total_rows,
                        "scheme_name": instance.scheme.scheme_name,
                        "file_name": instance.filename,
                    },
                )
                # instance.save()
            with open(tmpf.name, encoding=instance.encoding, errors="ignore") as cf:
                _process_csv_file(cf)

    except Exception:
        _l.debug("Can't process file", exc_info=True)
        instance.error_message = gettext_lazy("Invalid file format or file already deleted.")
    finally:
        storage.delete(instance.file_path)

    instance.error = (
        bool(instance.error_message) or (instance.error_row_index is not None) or bool(instance.error_rows)
    )

    return instance
