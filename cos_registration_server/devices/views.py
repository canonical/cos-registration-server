from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic

from .models import Device


class devices(generic.ListView):
    template_name = "devices/devices.html"
    context_object_name = "devices_list"

    def get_queryset(self):
        return Device.objects.all()


def device(request, uid):
    try:
        device = Device.objects.get(uid=uid)
    except Device.DoesNotExist:
        return HttpResponse(f"device {uid} not found")
    base_url = request.META["HTTP_HOST"]
    grafana_folder = base_url + "/cos-grafana/f/" + uid + "/"
    foxglove = (
        base_url
        + "/cos-foxglove-studio/?ds=foxglove-websocket&ds.url=ws%3A%2F%2F"
        + device.address
        + "%3A8765/"
    )
    bag_files = base_url + "/cos-ros2bag-fileserver/" + uid + "/"
    links = {
        "grafana folder": grafana_folder,
        "foxglove": foxglove,
        "bag_files": bag_files,
    }
    context = {
        "device": device,
        "links_dict": links,
    }
    return render(request, "devices/device.html", context)
