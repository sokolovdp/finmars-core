from __future__ import unicode_literals, print_function

from django.conf import settings
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject


class FileImportStorage(LazyObject):
    def _setup(self):
        clazz = get_storage_class(settings.FILE_IMPORT_STORAGE['BACKEND'])
        kwargs = settings.FILE_IMPORT_STORAGE['KWARGS'] or {}
        self._wrapped = clazz(**kwargs)

    def deconstruct(self):
        return 'poms.integrations.storage.FileImportStorage', [], {}


file_import_storage = FileImportStorage()


class ImportConfigStorage(LazyObject):
    def _setup(self):
        clazz = get_storage_class(settings.IMPORT_CONFIG_STORAGE['BACKEND'])
        kwargs = settings.IMPORT_CONFIG_STORAGE['KWARGS'] or {}
        self._wrapped = clazz(**kwargs)

    def deconstruct(self):
        return 'poms.integrations.storage.ImportConfigStorage', [], {}


import_config_storage = ImportConfigStorage()
