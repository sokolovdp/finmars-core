from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

DEBUG = messages.DEBUG
INFO = messages.INFO
SUCCESS = messages.SUCCESS
WARNING = messages.WARNING
ERROR = messages.ERROR

LEVELS = (
    (DEBUG, _('debug')),
    (INFO, _('info')),
    (SUCCESS, _('success')),
    (WARNING, _('warning')),
    (ERROR, _('error')),
)
