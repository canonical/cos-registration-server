"""Custom YAML field."""

from typing import Any, Dict

import yaml
from django.core.serializers.pyyaml import DjangoSafeDumper
from django.db import models
from rest_framework import serializers


class YAMLField(models.TextField):
    """A Django database field for storing YAML data."""

    def from_db_value(
        self, value: str, expression: Any, connection: Any, context=None
    ) -> Dict[str, Any]:
        """Retrieve python object from database."""
        return self.to_python(value)

    def to_python(self, value: str) -> Dict[str, Any]:
        """Convert YAML string to a Python object."""
        if value == "":
            return {}
        try:
            if isinstance(value, str):
                return yaml.load(value, yaml.SafeLoader)
        except ValueError:
            raise serializers.ValidationError("Provided YAML is invalid")

    def get_prep_value(self, value: Any) -> str:
        """Convert Python object to string of YAML."""
        if not value or value == "":
            return ""
        if isinstance(value, (dict, list)):
            value = yaml.dump(
                value, Dumper=DjangoSafeDumper, default_flow_style=False
            )
        return value

    def value_from_object(self, obj) -> str:
        """Return yaml str from python object.

        This must be override from the TextField,
        so that the YAML comes out properly formatted
        in the admin widget.
        """
        value = getattr(obj, self.attname)
        if not value or value == "":
            return value
        return yaml.dump(
            value, Dumper=DjangoSafeDumper, default_flow_style=False
        )
