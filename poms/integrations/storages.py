from __future__ import unicode_literals, print_function

from django.conf import settings
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


class FileImportStorage(LazyObject):
    def _setup(self):
        clazz = import_string(settings.FILE_IMPORT_STORAGE['BACKEND'])
        kwargs = settings.FILE_IMPORT_STORAGE['KWARGS'] or {}
        self._wrapped = clazz(**kwargs)

    def deconstruct(self):
        return 'poms.integrations.data_import.FileImportStorage', [], {}
