# Generated by Django 4.2.16 on 2025-01-29 10:48

from django.db import migrations, models
import django.utils.timezone
from datetime import timedelta

def set_default_expires_at(apps, schema_editor):
    Poll = apps.get_model("polls", "Poll")
    default_expiration = django.utils.timezone.now() + timedelta(days=7)

    # Update only polls that have NULL expires_at values
    Poll.objects.filter(expires_at__isnull=True).update(expires_at=default_expiration)

class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0005_poll_description'),
    ]

    operations = [
        migrations.RunPython(set_default_expires_at),
        migrations.AlterField(
            model_name="poll",
            name="expires_at",
            field=models.DateTimeField(default=django.utils.timezone.now() + timedelta(days=7)),
        ),
    ]
