"""Device DB model."""
from typing import Any, Dict, List

from django.db import models
from django.db.models.constraints import UniqueConstraint


def default_dashboards_json_field() -> List[Any]:
    """Return default value for dashboards.

    Default json values are usually dict but
    here we need a list
    """
    return []


def default_layouts_json_field() -> Dict[str, Any]:
    """Return default value for layouts."""
    return {}


class Device(models.Model):
    """Device model.

    This class represent a device in the DB.

    uid: Unique ID of the device.
    creation_date: Creation date of the device.
    address: IP address of the device.
    grafana_dashboards: list of Grafana dashboards.
    """

    uid = models.CharField(max_length=200)
    creation_date = models.DateTimeField("creation date", auto_now_add=True)
    address = models.GenericIPAddressField("device IP")
    grafana_dashboards = models.JSONField(
        "Grafana dashboards json field", default=default_dashboards_json_field
    )
    foxglove_layouts = models.JSONField(
        "Foxglove layouts json field", default=default_layouts_json_field
    )

    class Meta:
        """Model Meta class overwritting."""

        constraints = [
            UniqueConstraint(fields=["uid"], name="unique_uid_blocking")
        ]

    def __str__(self) -> str:
        """Str representation of a device."""
        return self.uid
