# Generated by Django 4.2.11 on 2024-03-19 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0002_foxglovedashboard"),
        ("devices", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="foxglove_dashboards",
            field=models.ManyToManyField(
                related_name="devices", to="applications.foxglovedashboard"
            ),
        ),
    ]