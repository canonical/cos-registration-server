"""API app serializer."""

import json
from typing import Any, Dict, Union

from applications.models import Dashboard, GrafanaDashboard
from devices.models import Device
from rest_framework import serializers


class DashboardSerializer:
    """Dashboard Serializer class."""

    class Meta:
        """DashboardSerializer Meta class."""

        model = Dashboard
        fields = ["uid", "dashboard"]

    def update(
        self, instance: Dashboard, validated_data: Dict[str, Any]
    ) -> Dashboard:
        """Update a Dashboard from data.

        instance: Device instance.
        validated_data: Dict of partial and validated data.
        """
        dashboard = validated_data.get("dashboard", instance.dashboard)
        instance.dashboard = dashboard
        instance.save()
        return instance

    def validate_dashboard(
        self, value: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate dashboards data.

        value: dashboard provided data.
        return: dashboard json.
        raise:
          json.JSONDecodeError
          serializers.ValidationError
        """
        if isinstance(value, str):
            try:
                dashboard = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "Failed to load dashboard as json."
                )
        else:
            dashboard = value
        if not isinstance(dashboard, dict):
            raise serializers.ValidationError(
                "Dashboard is not a supported format (dict)."
            )
        return dashboard


class GrafanaDashboardSerializer(
    DashboardSerializer, serializers.ModelSerializer  # type: ignore[type-arg]
):
    """Grafana Dashboard Serializer class."""

    class Meta(DashboardSerializer.Meta):
        """DashboardSerializer Meta class."""

        model = GrafanaDashboard

    def create(self, validated_data: Dict[str, Any]) -> GrafanaDashboard:
        """Create Grafana Dashboard object from data.

        validated_data: Dict of complete and validated data.
        """
        return GrafanaDashboard.objects.create(**validated_data)


class DeviceSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Device Serializer class."""

    grafana_dashboards = serializers.SlugRelatedField(
        many=True,
        queryset=GrafanaDashboard.objects.all(),
        slug_field="uid",
        required=False,
    )

    class Meta:
        """DeviceSerializer Meta class."""

        model = Device
        fields = ("uid", "creation_date", "address", "grafana_dashboards")

    def create(self, validated_data: Dict[str, Any]) -> Device:
        """Create Device object from data.

        validated_data: Dict of complete and validated data.
        """
        grafana_dashboards_data = validated_data.pop("grafana_dashboards", {})
        device = Device.objects.create(**validated_data)

        for dashboard_uid in grafana_dashboards_data:
            try:
                dashboard = GrafanaDashboard.objects.get(uid=dashboard_uid)
                device.grafana_dashboards.add(dashboard)
            except GrafanaDashboard.DoesNotExist:
                raise serializers.ValidationError(
                    f"GrafanaDashboard with UID {dashboard_uid}"
                    " does not exist."
                )
        return device

    def update(
        self, instance: Device, validated_data: Dict[str, Any]
    ) -> Device:
        """Update a Device from data.

        instance: Device instance.
        validated_data: Dict of partial and validated data.
        """
        # Update device fields (if any)
        for field, value in validated_data.items():
            if field != "grafana_dashboards":
                setattr(instance, field, value)
        instance.save()

        # Update Grafana dashboards
        try:
            grafana_dashboards_data = validated_data.pop("grafana_dashboards")
            current_grafana_dashboards = instance.grafana_dashboards.all()
            for dashboard in current_grafana_dashboards:
                instance.grafana_dashboards.remove(dashboard)

            for dashboard_uid in grafana_dashboards_data:
                try:
                    dashboard = GrafanaDashboard.objects.get(uid=dashboard_uid)
                    instance.grafana_dashboards.add(dashboard)
                except GrafanaDashboard.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Grafana Dashboard with UID {dashboard_uid}"
                        " does not exist."
                    )
        except KeyError:
            # Handle partial updates without grafana_dashboards vs
            # empty grafana_dashboards
            pass

        return instance
