import datetime
from dataclasses import asdict
from http import HTTPStatus

from django.utils.timezone import now
from rest_framework import exceptions
from rest_framework.status import is_client_error

from .models import ErrorRecord
from .settings import package_settings
from .types import (
    Error,
    ErrorResponse,
    ErrorResponseDetails,
    ErrorType,
    ExceptionHandlerContext,
)


class ExceptionFormatter:
    def __init__(
        self,
        exc: exceptions.APIException,
        context: ExceptionHandlerContext,
        original_exc: Exception,
    ):
        self.exc = exc
        self.context = context
        self.original_exc = original_exc

    def run(self):
        """
        Entrypoint for formatting the error response.

        The default error response format is as follows:
        - type: validation_error, client_error or server_error
        - errors: list of errors where each one has:
            - code: short string describing the error. Can be used by API consumers
            to customize their behavior.
            - detail: User-friendly text describing the error.
            - attr: set only when the error type is a validation error and maps
            to the serializer field name or NON_FIELD_ERRORS_KEY.

        Only validation errors can have multiple errors. Other error types have only
        one error.
        """
        error_type = self.get_error_type()
        errors = self.get_errors()

        url = str(self.context["request"].build_absolute_uri())[:255]
        method = str(self.context["request"].method)
        username = str(self.context["request"].user.username)[:255]
        status_code = self.exc.status_code
        http_code_to_message = {v.value: v.description for v in HTTPStatus}
        message = http_code_to_message[status_code]
        error_datetime = datetime.datetime.strftime(now(), "%Y-%m-%d %H:%M:%S")

        ErrorRecord.objects.create(
            url=url,
            username=username,
            status_code=self.exc.status_code,
            message=message,
            details=asdict(ErrorResponseDetails(error_type, errors)),
        )

        error_response = self.get_error_response(
            url, method, username, status_code, message, error_datetime, error_type, errors
        )

        return self.format_error_response(error_response)

    def get_error_type(self) -> ErrorType:
        if isinstance(self.exc, exceptions.ValidationError):
            return ErrorType.VALIDATION_ERROR
        elif is_client_error(self.exc.status_code):
            return ErrorType.CLIENT_ERROR
        else:
            return ErrorType.SERVER_ERROR

    def get_errors(self) -> list[Error]:
        """
        Account for validation errors in nested serializers by returning a list
        of errors instead of a nested dict
        """
        return flatten_errors(self.exc.detail)

    def get_error_response(
        self,
        url: str,
        method: str,
        username: str,
        status_code: int,
        message,
        error_datetime,
        error_type: ErrorType,
        errors: list[Error],
    ):
        error_response_details = ErrorResponseDetails(error_type, errors)

        return ErrorResponse(url, method, username, status_code, message, error_datetime, error_response_details)

    def format_error_response(self, error_response: ErrorResponse):
        return {"error": asdict(error_response)}


def flatten_errors(detail: list | dict | exceptions.ErrorDetail, attr=None, index=None) -> list[Error]:
    """
    convert this:
    {
        "password": [
            ErrorDetail("This password is too short.", code="password_too_short"),
            ErrorDetail("The password is too similar to the username.", code="password_too_similar"),
        ],
        "linked_accounts" [
            {},
            {"email": [ErrorDetail("Enter a valid email address.", code="invalid")]},
        ]
    }
    to:
    {
        "type": "validation_error",
        "errors": [
            {
                "code": "password_too_short",
                "detail": "This password is too short.",
                "attr": "password"
            },
            {
                "code": "password_too_similar",
                "detail": "The password is too similar to the username.",
                "attr": "password"
            },
            {
                "code": "invalid",
                "detail": "Enter a valid email address.",
                "attr": "linked_accounts.1.email"
            }
        ]
    }
    """

    if not detail:
        return []

    elif isinstance(detail, list):
        first_item, *rest = detail
        if isinstance(first_item, exceptions.ErrorDetail):
            return flatten_errors(first_item, attr, index) + flatten_errors(rest, attr, index)

        index = 0 if index is None else index + 1
        new_attr = f"{attr}{package_settings.NESTED_FIELD_SEPARATOR}{index}" if attr else str(index)

        return flatten_errors(first_item, new_attr, index) + flatten_errors(rest, attr, index)

    elif isinstance(detail, dict):
        (key, value), *rest = list(detail.items())
        if attr:
            key = f"{attr}{package_settings.NESTED_FIELD_SEPARATOR}{key}"
        return flatten_errors(value, key) + flatten_errors(dict(rest), attr)

    else:
        error_key = None

        if getattr(detail, "error_key", None):
            error_key = detail.error_key

        return [Error(detail.code, str(detail), error_key, attr)]
