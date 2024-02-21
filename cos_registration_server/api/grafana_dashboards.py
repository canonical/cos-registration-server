import json
from os import mkdir, remove
from pathlib import Path
from shutil import rmtree

from devices.models import Device
from django.conf import settings


def add_grafana_dashboards(device):
    dashboard_path = Path(settings.GRAFANA_DASHBOARD_PATH)
    for dashboard in device.grafana_dashboards:
        dashboard_title = dashboard["title"].replace(" ", "_")
        dashboard["title"] = f'{device.uid}-{dashboard["title"]}'
        dashboard_file = f"{device.uid}-{dashboard_title}.json"
        with open(dashboard_path / dashboard_file, "w") as file:
            json.dump(dashboard, file)


def delete_grafana_dashboards(device):
    dashboard_path = Path(settings.GRAFANA_DASHBOARD_PATH)

    def _is_device_dashboard(p: Path) -> bool:
        return p.is_file() and p.name.startswith(device.uid)

    for dashboard in filter(
        _is_device_dashboard, Path(dashboard_path).glob("*")
    ):
        remove(dashboard)


def update_all_grafana_dashboards():
    dashboard_path = Path(settings.GRAFANA_DASHBOARD_PATH)
    rmtree(dashboard_path, ignore_errors=True)
    mkdir(dashboard_path)
    for device in Device.objects.all():
        add_grafana_dashboards(device)
