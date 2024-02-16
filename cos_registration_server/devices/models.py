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


def default_layouts_json_field():
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

    def __str__(self):
        """Str representation of a device."""
        return self.uid

    def _validate_json_list_field(json_field):
        """Validate a json field as a list.

        raise:
          json.JSONDecodeError
          ValidationError
        """
        json_field_list = []
        if isinstance(json_field, str):
            try:
                json_field_list = json.loads(json_field)
            except json.JSONDecodeError:
                raise ValidationError(
                    f"Failed to load {json_field.name} as json"
                )
        elif isinstance(json_field, list):
            json_field_list = json_field
        else:
            raise ValidationError(
                f"Unknow type for {json_field.name}: \
                    {type(json_field)}"
            )

        if json_field_list is None or not isinstance(json_field_list, list):
            raise ValidationError(
                "{{json_field.name}} is not well formated. \
                    Make sure the field is a well formated json list."
            )
        return json_field_list

    def _validate_json_dict_field(json_field):
        """Validate a json field as a list.

        raise:
          json.JSONDecodeError
          ValidationError
        """
        json_field_dict = {}
        if isinstance(json_field, str):
            try:
                json_field_dict = json.loads(json_field)
            except json.JSONDecodeError:
                raise ValidationError(
                    f"Failed to load {json_field.name} as json"
                )
        elif isinstance(json_field, dict):
            json_field_dict = json_field
        else:
            raise ValidationError(
                f"Unknow type for {json_field.name}: \
                    {type(json_field)}"
            )

        if json_field_dict is None or not isinstance(json_field_dict, list):
            raise ValidationError(
                "{{json_field.name}} is not well formated. \
                    Make sure the field is a well formated json dict."
            )
        return json_field_dict

    def clean(self):
        """Model clean overwritting.

        Default Django model method to validate the model.
        Not automatically called.

        raise:
          json.JSONDecodeError
          ValidationError
        """
        # TODO To validate the dashboards and
        # layouts we might need json schema.

        # make sure the grafana_dashboards is containing an array of dashboards
        self._validate_json_field_list(self.grafana_dashboards)

        foxglove_layout_dict = self._validate_json_field_dict(
            self.foxglove_layouts
        )
        for key, value in foxglove_layout_dict:
            if not isinstance(key, str) or not isinstance(value, dict):
                raise ValidationError(
                    'Foxglove layouts should be passed with a name. \
                        {"my_name": {foxglove_layout...}}'
                )
