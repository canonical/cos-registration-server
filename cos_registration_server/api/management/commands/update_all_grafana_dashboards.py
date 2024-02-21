"""Update all dashboards django admin command."""
from api.grafana_dashboards import update_all_grafana_dashboards
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Update all Grafana dashboards command class."""

    help = "Update all the grafana dashboards in the folder"

    def handle(self, *args, **options):
        """Handle the call to update_all_grafana_dashboards command."""
        update_all_grafana_dashboards()
