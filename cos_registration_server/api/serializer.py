"""API app serializer."""

import json
from typing import Any, Dict, Union

import yaml
from applications.models import (
    AlertRuleFile,
    Dashboard,
    FoxgloveDashboard,
    GrafanaDashboard,
    PrometheusAlertRuleFile,
)
from applications.utils import is_alert_rule_a_jinja_template
from devices.models import Device
from django.core.serializers.pyyaml import DjangoSafeDumper
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

    prometheus_alert_rule_files = serializers.SlugRelatedField(
        many=True,
        queryset=PrometheusAlertRuleFile.objects.all(),
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
            "prometheus_alert_rule_files",
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
        prometheus_alert_rules_data = validated_data.pop(
            "prometheus_alert_rule_files", {}
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

        for rule_uid in prometheus_alert_rules_data:
            try:
                promethues_alert_rule = PrometheusAlertRuleFile.objects.get(
                    uid=rule_uid
                )
                device.prometheus_alert_rule_files.add(promethues_alert_rule)
            except PrometheusAlertRuleFile.DoesNotExist:
                raise serializers.ValidationError(
                    f"PrometheusAlertRuleFile with UID {dashboard_uid}"
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
            if field not in {
                "grafana_dashboards",
                "foxglove_dashboards",
                "prometheus_alert_rule_files",
            }:
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

        # Update Prometheus alert rules
        try:
            prometheus_alert_rules_data = validated_data.pop(
                "prometheus_alert_rule_files", {}
            )
            current_prometheus_alert_rule_files = (
                instance.prometheus_alert_rule_files.all()
            )
            for prometheus_alert_rule in current_prometheus_alert_rule_files:
                instance.prometheus_alert_rule_files.remove(
                    prometheus_alert_rule
                )

            for alert_rule_uid in prometheus_alert_rules_data:
                try:
                    prometheus_alert_rule = (
                        PrometheusAlertRuleFile.objects.get(uid=alert_rule_uid)
                    )
                    instance.prometheus_alert_rule_files.add(
                        prometheus_alert_rule
                    )
                except PrometheusAlertRuleFile.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Prometheus Alert Rule with UID {alert_rule_uid}"
                        " does not exist."
                    )
        except KeyError:
            # Handle partial updates without prometheus_alert_rule_files vs
            # empty prometheus_alert_rule_files
            pass
        return instance


class AlertRuleFileSerializer(
    serializers.ModelSerializer  # type: ignore[type-arg]
):
    """Alert rules file serializer class."""

    class Meta:
        """AlertRuleFileSerializer Meta class."""

        model = AlertRuleFile
        fields = ["uid", "rules", "template"]

    def to_representation(self, instance: AlertRuleFile) -> Dict[str, Any]:
        """Ensure that YAML data is properly serialized as a string.

        Overrides the default behavior to return the
        rules data correctly dumped as strings.

        instance: The AlertRuleFile model instance to be serialized.

        Returns a dictionary containing the serialized data
        with the rules dumped as strings.
        """
        data = super().to_representation(instance)
        yaml_data = getattr(instance, "rules", {})
        data["rules"] = yaml.dump(
            yaml_data, Dumper=DjangoSafeDumper, default_flow_style=False
        ).rstrip("\n")
        return data

    def update(
        self, instance: AlertRuleFile, validated_data: Dict[str, Any]
    ) -> AlertRuleFile:
        """Update an AlertRuleFile from data.

        instance: Device instance.
        validated_data: Dict of partial and validated data.
        """
        rules = validated_data.get("rules", instance.rules)
        instance.rules = rules
        instance.save()
        return instance

    def validate_rules(self, value: str) -> Dict[str, Any]:
        """Validate alert rules YAML rules.

        This validate function is called on is_valid()
        and validates the rules before saving them
        to database.

        value: YAML rules provided in string format.
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
            if not isinstance(alert_rule, dict):
                raise ValueError("YAML safe load must be a dictionary")
        except ValueError as e:
            raise serializers.ValidationError(
                f"Failed to load alert rule as a yaml: {e}"
            )
        return alert_rule


class PrometheusAlertRuleFileSerializer(
    AlertRuleFileSerializer,
):
    """Prometheus Alert Rule Serializer class."""

    class Meta(AlertRuleFileSerializer.Meta):
        """AlertRuleSerializer Meta class."""

        model = PrometheusAlertRuleFile

    def create(
        self, validated_data: Dict[str, Any]
    ) -> PrometheusAlertRuleFile:
        """Create PrometheusAlertRuleFile object from data.

        validated_data: Dict of complete JSON validated data
        provided by the request.
        In the alert rule case a valid data request is:
            json = {
              uid = "rule_uid"
              rules = file(rules.rule)
            }
        """
        is_template = is_alert_rule_a_jinja_template(validated_data["rules"])

        # Add template key to the validated_data, this is available
        # in the model but not exposed in the API
        validated_data["template"] = is_template
        return PrometheusAlertRuleFile.objects.create(**validated_data)
