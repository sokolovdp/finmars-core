from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("csv_import", "0014_csvimportscheme_actual_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="entityfield",
            name="classifier_handler",
            field=models.CharField(
                blank=True,
                choices=[("skip", "Skip"), ("append", "Append")],
                default=None,
                max_length=255,
                null=True,
            ),
        ),
    ]
