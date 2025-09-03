from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Move input settings"

    def handle(self, *args, **options):
        from django.contrib.contenttypes.models import ContentType

        from poms.ui.models import EditLayout
        from poms.users.models import Member

        content_types = ContentType.objects.all()

        members = Member.objects.all()

        count = 0

        for member in members:
            for content_type in content_types:
                layouts = EditLayout.objects.filter(member=member, content_type=content_type, is_default=True)

                if len(layouts) == 0:
                    layouts = EditLayout.objects.filter(member=member, content_type=content_type)

                    if len(layouts):
                        layout = layouts[0]
                        layout.is_default = True
                        layout.save()
                        count = count + 1

        self.stdout.write(f"Job Done. Layouts Affected {count}")
