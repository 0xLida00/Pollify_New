# Generated by Django 4.2.16 on 2025-01-29 13:49

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0008_alter_poll_expires_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='expires_at',
            field=models.DateTimeField(default=datetime.datetime(2025, 2, 5, 13, 49, 6, 206060, tzinfo=datetime.timezone.utc)),
        ),
    ]
