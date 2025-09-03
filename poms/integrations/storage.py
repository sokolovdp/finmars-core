from django.conf import settings
from django.core.files.storage import get_storage_class
from django.utils.functional import LazyObject


# DEPRECATED, DELETE SOON
class ImportFileStorage(LazyObject):
    def _setup(self):
        clazz = get_storage_class(settings.IMPORT_FILE_STORAGE["BACKEND"])
        kwargs = settings.IMPORT_FILE_STORAGE["KWARGS"] or {}
        self._wrapped = clazz(**kwargs)

    def deconstruct(self):
        return "poms.integrations.storage.ImportFileStorage", [], {}


import_file_storage = ImportFileStorage()


# DEPRECATED, DELETE SOON
class ImportConfigStorage(LazyObject):
    def _setup(self):
        pass
        # clazz = get_storage_class(settings.IMPORT_CONFIG_STORAGE['BACKEND'])
        # kwargs = settings.IMPORT_CONFIG_STORAGE['KWARGS'] or {}
        # self._wrapped = clazz(**kwargs)

    def deconstruct(self):
        return "poms.integrations.storage.ImportConfigStorage", [], {}


import_config_storage = ImportConfigStorage()
