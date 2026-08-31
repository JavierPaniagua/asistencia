from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("asistencia", "0005_claseactiva"),
    ]

    operations = [
        migrations.AddField(
            model_name="claseactiva",
            name="finalizada",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
    ]