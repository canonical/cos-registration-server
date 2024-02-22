"""Devices views."""
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.http import urlencode
from django.views import generic

from .models import Device


class devices(generic.ListView):
    """Devices list view."""

    template_name = "devices/devices.html"
    context_object_name = "devices_list"

    def get_queryset(self):
        """Return all devices on GET."""
        return Device.objects.all()


def device(request, uid):
    """Device view.

    Representation of the device.

    uid: uid of the device passed by url.
    return: Http Response.
    """
    try:
        device = Device.objects.get(uid=uid)
    except Device.DoesNotExist:
        return HttpResponse(f"device {uid} not found")

    class ApplicationLinks:
        """Application links structure.

        This class is holding the links of an application
        so it can be passed to the html template.

        params:
            name: Name of the application.
            main_link: Main link of the application.
            additional_links: Additional links of the application
                    (dashboards etc).
        """

        def __init__(self, name, main_link, additional_links={}) -> None:
            self.name = name
            self.main_link = main_link
            self.additional_links = additional_links

    base_url = request.META["HTTP_HOST"]

    grafana_param = {"query": uid}
    grafana_main_link = (
        f"{base_url}/cos-grafana/dashboards/?{urlencode(grafana_param)}/"
    )
    grafana_dashboards = {}
    for dashboards in device.grafana_dashboards:
        if dashboard_uid := dashboards.get("uid"):
            title = dashboards.get("title", dashboard_uid)
            grafana_dashboards[title] = (
                base_url + "/cos-grafana/dashboards/" + dashboard_uid + "/"
            )

    foxglove_params = {
        "ds": "foxglove-websocket",
        "ds.url": f"ws://{device.address}:8765",
    }
    foxglove_main_link = (
        f"{base_url}/cos-foxglove-studio/?{urlencode(foxglove_params)}"
    )
    foxglove_layouts = {}
    for name in device.foxglove_layouts.keys():
        foxglove_params["layoutUrl"] = (
            f"{base_url}/cos-cos-registration-server/api/v1/"
            f"devices/{uid}/foxglove_layouts/{name}"
        )
        foxglove_layouts[
            name
        ] = f"{base_url}/cos-foxglove-studio/?{urlencode(foxglove_params)}"

    bag_files = f"{base_url}/cos-ros2bag-fileserver/{uid}/"

    links = []
    links.append(
        ApplicationLinks(
            "Foxglove studio", foxglove_main_link, foxglove_layouts
        )
    )
    links.append(
        ApplicationLinks("Grafana", grafana_main_link, grafana_dashboards)
    )
    links.append(ApplicationLinks("Bag files", bag_files))
    context = {
        "device": device,
        "links_list": links,
    }
    return render(request, "devices/device.html", context)
