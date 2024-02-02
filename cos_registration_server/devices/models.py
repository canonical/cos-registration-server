import json

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint


def default_dashboards_json_field():
    return []


class Device(models.Model):
    uid = models.CharField(max_length=200)
    creation_date = models.DateTimeField("creation date", auto_now_add=True)
    address = models.GenericIPAddressField("device IP")
    grafana_dashboards = models.JSONField(
        "Dashboards json field", default=default_dashboards_json_field
    )

    def __str__(self):
        return self.uid

    class Meta:
        constraints = [
            UniqueConstraint(fields=["uid"], name="unique_uid_blocking")
        ]

    def clean(self):
        # make sure the grafana_dashboards is containing an array of dashboards
        dashboards = []
        if isinstance(self.grafana_dashboards, str):
            try:
                dashboards = json.loads(self.grafana_dashboards)
            except json.JSONDecodeError:
                raise ValidationError(
                    "Failed to load grafana_dashboards as json"
                )
        elif isinstance(self.grafana_dashboards, list):
            dashboards = self.grafana_dashboards
        else:
            raise ValidationError(
                f"Unknow type for grafana_dashboards: \
                    {type(self.grafana_dashboards)}"
            )

        if dashboards is None or not isinstance(dashboards, list):
            raise ValidationError(
                'gafana_dashboards is not well formated. \
                    Make sure all the dashboards are within "dashbords": [] '
            )
