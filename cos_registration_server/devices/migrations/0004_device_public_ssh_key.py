# Generated by Django 4.2.10 on 2024-02-26 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("devices", "0003_device_foxglove_layouts_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="public_ssh_key",
            field=models.CharField(max_length=2000),
        ),
    ]