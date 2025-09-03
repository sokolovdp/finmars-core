from django.core.management import BaseCommand

__author__ = "szhitenev"


class Command(BaseCommand):
    help = "Get Fancy Name"

    def handle(self, *args, **options):
        from haikunator import Haikunator

        haikunator = Haikunator()
        worker_name = haikunator.haikunate(delimiter="-", token_length=0)

        return worker_name
