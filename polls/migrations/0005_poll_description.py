# Generated by Django 4.2.16 on 2025-01-28 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0004_alter_poll_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
