import os
import traceback

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from poms.common.storage import get_storage


class Command(BaseCommand):
    help = "Encrypts all files in storage"

    def handle(self, *args, **options):
        # Generate a new symmetric key
        symmetric_key = bytes.fromhex(settings.ENCRYPTION_KEY)

        storage = get_storage()
        # Save the keys to Vault or any other secure storage
        # You can use the Vault client or any other library to store the keys securely

        from poms.users.models import MasterUser

        master_user = MasterUser.objects.all().first()
        # Encrypt files recursively
        try:
            self.encrypt_files_recursively(storage, symmetric_key, master_user.space_code)
        except Exception as e:
            print(f"Error encrypting files: {traceback.format_exc()}")
            print(f"Error encrypting files: {e}")

        self.stdout.write(self.style.SUCCESS("All files have been encrypted."))

    def encrypt_files_recursively(self, storage, symmetric_key, directory):
        files = storage.listdir(directory)[1]
        for file_name in files:
            file_path = os.path.join(directory, file_name)

            print(f"File_path {file_path}")

            if ".system/vault" not in file_path:  # TODO be careful about another services
                file = storage.open_skip_decrypt(file_path, "rb")
                file_content = ContentFile(file.read())
                storage.save(file_path, file_content)

        # Encrypt files within subdirectories
        subdirectories = storage.listdir(directory)[0]
        for subdirectory in subdirectories:
            subdirectory_path = os.path.join(directory, subdirectory)
            print(f"subdirectory {subdirectory_path}")
            self.encrypt_files_recursively(storage, symmetric_key, subdirectory_path)
