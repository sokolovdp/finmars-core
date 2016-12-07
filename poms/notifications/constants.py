from django.contrib import messages
from django.utils.translation import ugettext_lazy

DEBUG = messages.DEBUG
INFO = messages.INFO
SUCCESS = messages.SUCCESS
WARNING = messages.WARNING
ERROR = messages.ERROR

LEVELS = (
    (DEBUG, ugettext_lazy('debug')),
    (INFO, ugettext_lazy('info')),
    (SUCCESS, ugettext_lazy('success')),
    (WARNING, ugettext_lazy('warning')),
    (ERROR, ugettext_lazy('error')),
)
