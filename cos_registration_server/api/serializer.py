"""API app serializer."""

import json
import yaml
from typing import (
    Any,
    Dict,
    Union,
)

from applications.models import (
    Dashboard,
    FoxgloveDashboard,
    GrafanaDashboard,
    AlertRule,
    PrometheusAlertRule,
)
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


class FoxgloveDashboardSerializer(
    DashboardSerializer, serializers.ModelSerializer  # type: ignore[type-arg]
):
    """Foxglove Dashboard Serializer class."""

    class Meta(DashboardSerializer.Meta):
        """DashboardSerializer Meta class."""

        model = FoxgloveDashboard

    def create(self, validated_data: Dict[str, Any]) -> FoxgloveDashboard:
        """Create Foxglove Dashboard object from data.

        validated_data: Dict of complete and validated data.
        """
        return FoxgloveDashboard.objects.create(**validated_data)


class DeviceSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    """Device Serializer class."""

    grafana_dashboards = serializers.SlugRelatedField(
        many=True,
        queryset=GrafanaDashboard.objects.all(),
        slug_field="uid",
        required=False,
    )

    foxglove_dashboards = serializers.SlugRelatedField(
        many=True,
        queryset=FoxgloveDashboard.objects.all(),
        slug_field="uid",
        required=False,
    )

    class Meta:
        """DeviceSerializer Meta class."""

        model = Device
        fields = (
            "uid",
            "creation_date",
            "address",
            "public_ssh_key",
            "grafana_dashboards",
            "foxglove_dashboards",
        )

    def to_representation(self, instance: Device) -> Dict[str, Any]:
        """Repesent filter by fields serialized data.

        Overrides the default behavior to return a
        dictionary containing only the fields
        specified in the URL parameter 'fields' (comma-separated list).
        If no 'fields' parameter is provided,
        returns the entire serialized data.

        instance: The Device model instance to be serialized.

        Returns a dictionary containing the requested or
        all fields of the serialized data.
        """
        data = super().to_representation(instance)
        if request := self.context.get("request"):
            if requested_fields := request.query_params.get("fields"):
                return {
                    field: data[field] for field in requested_fields.split(",")
                }

        return data

    def create(self, validated_data: Dict[str, Any]) -> Device:
        """Create Device object from data.

        validated_data: Dict of complete and validated data.
        """
        grafana_dashboards_data = validated_data.pop("grafana_dashboards", {})
        foxglove_dashboards_data = validated_data.pop(
            "foxglove_dashboards", {}
        )
        device = Device.objects.create(**validated_data)

        for dashboard_uid in grafana_dashboards_data:
            try:
                grafana_dashboard = GrafanaDashboard.objects.get(
                    uid=dashboard_uid
                )
                device.grafana_dashboards.add(grafana_dashboard)
            except GrafanaDashboard.DoesNotExist:
                raise serializers.ValidationError(
                    f"GrafanaDashboard with UID {dashboard_uid}"
                    " does not exist."
                )
        for dashboard_uid in foxglove_dashboards_data:
            try:
                foxglove_dashboard = FoxgloveDashboard.objects.get(
                    uid=dashboard_uid
                )
                device.foxglove_dashboards.add(foxglove_dashboard)
            except FoxgloveDashboard.DoesNotExist:
                raise serializers.ValidationError(
                    f"FoxgloveDashboard with UID {dashboard_uid}"
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
            if field not in {"grafana_dashboards", "foxglove_dashboards"}:
                setattr(instance, field, value)
        instance.save()

        # Update Grafana dashboards
        try:
            grafana_dashboards_data = validated_data.pop("grafana_dashboards")
            current_grafana_dashboards = instance.grafana_dashboards.all()
            for grafana_dashboard in current_grafana_dashboards:
                instance.grafana_dashboards.remove(grafana_dashboard)

            for dashboard_uid in grafana_dashboards_data:
                try:
                    grafana_dashboard = GrafanaDashboard.objects.get(
                        uid=dashboard_uid
                    )
                    instance.grafana_dashboards.add(grafana_dashboard)
                except GrafanaDashboard.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Grafana Dashboard with UID {dashboard_uid}"
                        " does not exist."
                    )
        except KeyError:
            # Handle partial updates without grafana_dashboards vs
            # empty grafana_dashboards
            pass

        # Update Foxglove dashboards
        try:
            foxglove_dashboards_data = validated_data.pop(
                "foxglove_dashboards"
            )
            current_foxglove_dashboards = instance.foxglove_dashboards.all()
            for foxglove_dashboard in current_foxglove_dashboards:
                instance.foxglove_dashboards.remove(foxglove_dashboard)

            for dashboard_uid in foxglove_dashboards_data:
                try:
                    foxglove_dashboard = FoxgloveDashboard.objects.get(
                        uid=dashboard_uid
                    )
                    instance.foxglove_dashboards.add(foxglove_dashboard)
                except FoxgloveDashboard.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Foxglove Dashboard with UID {dashboard_uid}"
                        " does not exist."
                    )
        except KeyError:
            # Handle partial updates without foxglove_dashboards vs
            # empty foxglove_dashboards
            pass

        return instance


class AlertRuleSerializer:
    """Alert rules Serializer class."""

    class Meta:
        """AlertRuleSerializer Meta class."""

        model = AlertRule
        fields = ["uid", "rules"]

    def update(
        self, instance: AlertRule, validated_data: Dict[str, Any]
    ) -> AlertRule:
        """Update an AlertRule from data.

        instance: Device instance.
        validated_data: Dict of partial and validated data.
        """
        rules = validated_data.get("rules", instance.rules)
        instance.rules = rules
        instance.save()
        return instance

    def validate_rules(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Validate alert rules YAML rules.

        This validate function is called on is_valid()
        and validates the rules before saving them
        database and sending them.

        value: YAML rules provided in python object format.
        return: dashboard json.
        raise:
          yaml.YAMLError
          serializers.ValidationError
        """
        if not isinstance(value, str):
            raise serializers.ValidationError(
                "Alert rule is not a supported format (str)."
            )
        try:
            alert_rule = yaml.safe_load(value)
        except yaml.YAMLError as e:
            raise serializers.ValidationError(
                f"Failed to load alert rule as a yaml: {e}"
            )
        return alert_rule


class PrometheusAlertRuleSerializer(
    AlertRuleSerializer, serializers.ModelSerializer  # type: ignore[type-arg]
):
    """Prometheus Alert Rule Serializer class."""

    class Meta(AlertRuleSerializer.Meta):
        """AlertRuleSerializer Meta class."""

        model = PrometheusAlertRule

    # here we get the FUll JSON from request
    def create(self, validated_data: Dict[str, Any]) -> PrometheusAlertRule:
        """Create PrometheusAlertRule object from data.

        validated_data: Dict of complete JSON validated data
        provided by the request.
        In the alert rule case a valid data request is:
            json = {
            uid = "rule_uid"
            rules = file(rules.rule)
            }
        """
        # TODO: here we do the rendering of the incoming jinja rules
        # template_bool = jinja_render(validated_data["rules"])
        # validated_data["template_bool"] = template_bool
        return PrometheusAlertRule.objects.create(**validated_data)
