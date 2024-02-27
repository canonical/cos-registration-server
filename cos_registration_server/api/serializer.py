"""API app serializer."""
import json

from devices.models import Device
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class DeviceSerializer(serializers.Serializer):
    """Device Serializer class."""

    uid = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=Device.objects.all())],
    )
    creation_date = serializers.DateTimeField(read_only=True)
    address = serializers.IPAddressField(required=True)
    grafana_dashboards = serializers.JSONField(required=False)
    foxglove_layouts = serializers.JSONField(required=False)
    public_ssh_key = serializers.CharField(required=True)

    def create(self, validated_data):
        """Create Device object from data.

        validated_data: Dict of complete and validated data.
        """
        return Device.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update a Device from data.

        instance: Device instance.
        validated_data: Dict of partial and validated data.
        """
        address = validated_data.get("address", instance.address)
        instance.address = address
        grafana_dashboards = validated_data.get(
            "grafana_dashboards", instance.grafana_dashboards
        )
        instance.grafana_dashboards = grafana_dashboards
        foxglove_layouts = validated_data.get(
            "foxglove_layouts", instance.foxglove_layouts
        )
        instance.foxglove_layouts = foxglove_layouts
        instance.save()
        return instance

    def validate_grafana_dashboards(self, value):
        """Validate grafana dashboards data.

        value: Grafana dashboards provided data.
        return: Grafana dashboards as list.
        raise:
          json.JSONDecodeError
          serializers.ValidationError
        """
        if isinstance(value, str):
            try:
                dashboards = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "Failed to load grafana_dashboards as json."
                )
        else:
            dashboards = value
        if not isinstance(dashboards, list):
            raise serializers.ValidationError(
                "gafana_dashboards is not a supported format (list)."
            )
        return dashboards

    def validate_foxglove_layouts(self, value):
        """Validate foxglove layouts data.

        value: Foxglove layouts provided data.
        return: Foxglove layouts as dict.
        raise:
          json.JSONDecodeError
          serializers.ValidationError
        """
        if isinstance(value, str):
            try:
                layouts = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "Failed to load foxglove_layouts as json."
                )
        else:
            layouts = value
        if not isinstance(layouts, dict):
            raise serializers.ValidationError(
                "foxglove_layouts is not a supported format (dict)."
            )

        for key, value in layouts.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                raise serializers.ValidationError(
                    'foxglove_layouts should be passed with a name. \
                    {"my_name": {foxglove_layout...} }'
                )

        return layouts
