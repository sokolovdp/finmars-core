import uuid

from django.core.management import BaseCommand

__author__ = 'ailyukhin'


class Command(BaseCommand):
    help = 'Create empty master user'

    def handle(self, *args, **options):
        from poms.users.models import MasterUser
        name = str(uuid.uuid4())
        MasterUser.objects.create_master_user(name=name)
        self.stdout.write("Master user '%s' created." % name)
