from django.core.management import BaseCommand
from django.utils import timezone

__author__ = 'ailyukhin'


class Command(BaseCommand):
    help = 'Create empty master user'

    def handle(self, *args, **options):
        from poms.users.models import MasterUser
        MasterUser.objects.create_master_user(
            name='%s' % timezone.now()
        )
