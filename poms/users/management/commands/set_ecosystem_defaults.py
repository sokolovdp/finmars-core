from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set Master Users Tokens"

    def handle(self, *args, **options):
        from poms.instruments.models import PricingCondition
        from poms.users.models import EcosystemDefault

        items = EcosystemDefault.objects.all()

        count = 0

        for item in items:
            if not item.pricing_condition:
                item.pricing_condition = PricingCondition.objects.get(id=PricingCondition.NO_VALUATION)

                count = count + 1

                item.save()

        self.stdout.write(f"Job Done. Ecosystems Affected {count}")
