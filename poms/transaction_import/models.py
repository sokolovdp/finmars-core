import logging

_l = logging.getLogger("poms.transaction_import")


class ProcessType:
    CSV = "CSV"
    JSON = "JSON"
    EXCEL = "EXCEL"


class TransactionImportBookedTransaction:
    def __init__(self, code=None, text=None, transaction_unique_code=None):
        self.code = code
        self.text = text
        self.transaction_unique_code = transaction_unique_code


class TransactionImportConversionItem:
    def __init__(self, file_inputs=None, raw_inputs=None, conversion_inputs=None, row_number=None):
        self.file_inputs = file_inputs
        self.raw_inputs = raw_inputs
        self.conversion_inputs = conversion_inputs
        self.row_number = row_number


class TransactionImportProcessPreprocessItem:
    def __init__(
        self,
        file_inputs=None,
        raw_inputs=None,
        conversion_inputs=None,
        inputs=None,
        row_number=None,
    ):
        self.file_inputs = file_inputs
        self.raw_inputs = raw_inputs
        self.conversion_inputs = conversion_inputs
        self.inputs = inputs
        self.row_number = row_number


class TransactionImportProcessItem:
    def __init__(
        self,
        status="init",
        error_message=None,
        message="",
        processed_rule_scenarios=None,
        booked_transactions=None,
        file_inputs=None,
        raw_inputs=None,
        inputs=None,
        transaction_inputs=None,
        row_number=None,
    ):
        self.file_inputs = file_inputs
        self.raw_inputs = raw_inputs
        self.inputs = inputs
        self.transaction_inputs = transaction_inputs
        self.row_number = row_number
        self.status = status
        self.error_message = error_message
        self.message = message
        self.processed_rule_scenarios = processed_rule_scenarios
        self.booked_transactions = booked_transactions


class TransactionImportResult:
    def __init__(
        self,
        task=None,
        scheme=None,
        file_name=None,
        file_path=None,
        total_rows=None,
        processed_rows=0,
        errors=None,
        items=None,
        error_message=None,
        reports=None,
    ):
        self.task = task
        self.scheme = scheme
        self.file_name = file_name
        self.total_rows = total_rows
        self.processed_rows = processed_rows
        self.items = items
        self.file_path = file_path
        self.errors = errors
        self.error_message = error_message
        self.reports = reports
