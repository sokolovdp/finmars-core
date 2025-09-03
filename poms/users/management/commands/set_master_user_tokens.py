from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set Master Users Tokens"

    def handle(self, *args, **options):
        import uuid

        from poms.users.models import MasterUser

        master_users = MasterUser.objects.all()

        count = 0

        for master_user in master_users:
            if not master_user.token:
                try:
                    token = uuid.uuid4().hex

                    master_user.token = token

                    master_user.save()
                    count = count + 1

                except Exception as e:
                    self.stdout.write(f"Error occurred. master_user id {master_user.id}")
                    self.stdout.write(f"Error occurred. e {e}")

        self.stdout.write(f"Job Done. Master Users Affected {count}")
