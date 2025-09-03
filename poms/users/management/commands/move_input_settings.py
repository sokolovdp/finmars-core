from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Move input settings"

    def handle(self, *args, **options):
        from poms.transactions.models import TransactionTypeInput

        inputs = TransactionTypeInput.objects.all()

        count = 0

        for input in inputs:
            old_settings = input.settings_old.last()

            if old_settings:
                input.settings = old_settings

                count = count + 1

                input.save()

        self.stdout.write(f"Job Done. Inputs Affected {count}")
