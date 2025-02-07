"""Custom YAML field.

TODO: add a license, this code was taken from
https://github.com/palewire/django-yamlfield
"""

from typing import Any, Optional

import yaml
from django.core.serializers.pyyaml import DjangoSafeDumper
from django.db import models
from rest_framework import serializers


class YAMLField(models.TextField):  # type: ignore[type-arg]
    """A Django database field for storing YAML data."""

    def from_db_value(
        self,
        value: str,
        expression: Any,
        connection: Any,
        context: Optional[Any] = None,
    ) -> Any:
        """Retrieve python object from database."""
        return self.to_python(value)

    def to_python(self, value: str) -> Any:
        """Convert YAML string to a Python object."""
        if value == "":
            return {}
        if isinstance(value, str):
            try:
                return yaml.load(value, yaml.SafeLoader)
            except ValueError:
                raise serializers.ValidationError("Provided YAML is invalid")

    def get_prep_value(self, value: Any) -> Any:
        """Convert Python object to string of YAML."""
        if not value:
            return ""
        if isinstance(value, (dict, list)):
            value = yaml.dump(
                value, Dumper=DjangoSafeDumper, default_flow_style=False
            )
        return value

    def value_from_object(self, obj: Any) -> Any:
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
