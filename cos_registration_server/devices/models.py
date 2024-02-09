"""Device DB model."""
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.constraints import UniqueConstraint


def default_dashboards_json_field():
    """Return default value for dashboards.

    Default json values are usually dict but
    here we need a list
    """
    return []


class Device(models.Model):
    """Device model.

    This class represent a device in the DB.

    uid: Unique ID of the device.
    creation_data: Creation date of the device.
    address: IP address of the device.
    grafana_dashboards: list of Grafana dashboards.
    """

    uid = models.CharField(max_length=200)
    creation_date = models.DateTimeField("creation date", auto_now_add=True)
    address = models.GenericIPAddressField("device IP")
    grafana_dashboards = models.JSONField(
        "Dashboards json field", default=default_dashboards_json_field
    )

    class Meta:
        """Model Meta class overwritting."""

        constraints = [
            UniqueConstraint(fields=["uid"], name="unique_uid_blocking")
        ]

    def __str__(self):
        """Str representation of a device."""
        return self.uid

    def clean(self):
        """Model clean overwritting.

        Default Django model method to validate the model.
        Not automatically called.

        raise:
          json.JSONDecodeError
          ValidationError
        """
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
