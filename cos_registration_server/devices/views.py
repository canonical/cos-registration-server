"""Devices views."""

from typing import Any, Dict

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.http import urlencode
from django.views import generic

from .models import Device


class devices(generic.ListView):  # type: ignore[type-arg]
    """Devices list view."""

    template_name = "devices/devices.html"
    context_object_name = "devices_list"
    paginate_by = 25

    def get_queryset(self) -> Any:
        """Return all devices on GET."""
        return Device.objects.all()


def device(request: HttpRequest, uid: str) -> HttpResponse:
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

        def __init__(
            self,
            name: str,
            main_link: str,
            additional_links: Dict[str, str] = {},
        ) -> None:
            self.name = name
            self.main_link = main_link
            self.additional_links = additional_links

    base_url = request.META["HTTP_HOST"]

    cos_model_name = settings.COS_MODEL_NAME

    # fmt: off
    grafana_main_link = (
        f"{base_url}/{cos_model_name}-grafana/"
        f"dashboards/"
    )
    # fmt: on

    grafana_dashboards = {}
    grafana_param = {"var-Host": uid}
    for grafana_dashboard in device.grafana_dashboards.all():
        grafana_dashboards[grafana_dashboard.uid] = (
            base_url
            + f"/{cos_model_name}-grafana/d/"
            + grafana_dashboard.uid
            + "/"
            f"?{urlencode(grafana_param)}"
        )

    websocket_scheme = "wss" if request.scheme == "https" else "ws"

    foxglove_params = {
        "ds": "foxglove-websocket",
        "ds.url": f"{websocket_scheme}://{device.address}:8765",
    }
    foxglove_main_link = (
        f"{base_url}/"
        f"{cos_model_name}-foxglove-studio/?{urlencode(foxglove_params)}"
    )
    foxglove_layouts = {}
    for foxglove_dashboard in device.foxglove_dashboards.all():
        foxglove_params["layoutUrl"] = (
            f"{base_url}/{cos_model_name}-cos-registration-server/api/v1/"  # noqa: E501
            f"applications/foxglove/dashboards/{foxglove_dashboard.uid}"
        )
        foxglove_layouts[foxglove_dashboard.uid] = (
            f"{base_url}/{cos_model_name}-foxglove-studio/"
            f"?{urlencode(foxglove_params)}"
        )

    bag_files = f"{base_url}/{cos_model_name}-ros2bag-fileserver/{uid}/"

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
