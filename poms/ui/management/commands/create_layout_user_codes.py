from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Copy Name To User Code if not exist"

    def handle(self, *args, **options):  # noqa: PLR0912, PLR0915
        from poms.ui.models import ListLayout

        list_layouts = ListLayout.objects.all()

        count = 0

        for layout in list_layouts:
            if not layout.user_code:
                try:
                    if len(layout.name) > 23:
                        layout.user_code = layout.name[:23]

                    else:
                        layout.user_code = layout.name

                    layout.save()
                    count = count + 1

                except Exception as e:
                    self.stdout.write(f"Error occurred. Layout id {layout.id}")
                    self.stdout.write(f"Error occurred. e {e}")

        self.stdout.write(f"Job Done. ListLayout Affected {count}")

        from poms.ui.models import ContextMenuLayout

        list_layouts = ContextMenuLayout.objects.all()

        count = 0

        for layout in list_layouts:
            if not layout.user_code:
                try:
                    if len(layout.name) > 23:
                        layout.user_code = layout.name[:23]

                    else:
                        layout.user_code = layout.name

                    layout.save()
                    count = count + 1

                except Exception as e:
                    self.stdout.write(f"Error occurred. Layout id {layout.id}")
                    self.stdout.write(f"Error occurred. e {e}")
                    pass

        self.stdout.write(f"Job Done. ContextMenuLayout Affected {count}")

        from poms.ui.models import DashboardLayout

        list_layouts = DashboardLayout.objects.all()

        count = 0

        for layout in list_layouts:
            if not layout.user_code:
                try:
                    if len(layout.name) > 23:
                        layout.user_code = layout.name[:23]

                    else:
                        layout.user_code = layout.name

                    layout.save()
                    count = count + 1

                except Exception as e:
                    self.stdout.write(f"Error occurred. Layout id {layout.id}")
                    self.stdout.write(f"Error occurred. e {e}")

                    pass

        self.stdout.write(f"Job Done. DashboardLayout Affected {count}")

        from poms.ui.models import TemplateLayout

        list_layouts = TemplateLayout.objects.all()

        count = 0

        for layout in list_layouts:
            if not layout.user_code:
                try:
                    if len(layout.name) > 23:
                        layout.user_code = layout.name[:23]

                    else:
                        layout.user_code = layout.name

                    layout.save()
                    count = count + 1

                except Exception as e:
                    self.stdout.write(f"Error occurred. Layout id {layout.id}")
                    self.stdout.write(f"Error occurred. e {e}")
                    pass

        self.stdout.write(f"Job Done. TemplateLayout Affected {count}")
