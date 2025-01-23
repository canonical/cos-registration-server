import yaml
from typing import Any, Dict
from django.db import models

from django.core.serializers.pyyaml import DjangoSafeDumper
from rest_framework import serializers

class YAMLField(models.TextField):
    def from_db_value(self, value: str, expression: Any, connection: Any, context=None) -> Dict[str, Any]:
        return self.to_python(value)

    def to_python(self, value: str) -> Dict[str, Any]:
        """
        Convert our YAML string to a Python object
        after we load it from the DB.
        """
        if value == "":
            return {}
        try:
            if isinstance(value, str):
                return yaml.load(value, yaml.SafeLoader)
        except ValueError:
            raise serializers.ValidationError("Provided YAML is invalid")

    def get_prep_value(self, value: Any) -> str:
        """
        Convert our Python object to a string of YAML before we save.
        """
        if not value or value == "":
            return ""
        if isinstance(value, (dict, list)):
            value = yaml.dump(value, Dumper=DjangoSafeDumper, default_flow_style=False)
        return value

    def value_from_object(self, obj) -> str:
        """
        Returns the value of this field in the given model instance.

        We need to override this so that the YAML comes out properly formatted
        in the admin widget.
        """
        value = getattr(obj, self.attname)
        if not value or value == "":
            return value
        return yaml.dump(value, Dumper=DjangoSafeDumper, default_flow_style=False)
