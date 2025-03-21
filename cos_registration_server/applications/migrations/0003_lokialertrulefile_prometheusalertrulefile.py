# Generated by Django 4.2.18 on 2025-01-30 14:28

import applications.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0002_foxglovedashboard"),
    ]

    operations = [
        migrations.CreateModel(
            name="LokiAlertRuleFile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("uid", models.CharField(max_length=200, unique=True)),
                ("rules", applications.fields.YAMLField()),
                (
                    "template",
                    models.BooleanField(
                        default=False,
                        verbose_name="Whether this rules file is                                    a template and must be rendered",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PrometheusAlertRuleFile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("uid", models.CharField(max_length=200, unique=True)),
                ("rules", applications.fields.YAMLField()),
                (
                    "template",
                    models.BooleanField(
                        default=False,
                        verbose_name="Whether this rules file is                                    a template and must be rendered",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
