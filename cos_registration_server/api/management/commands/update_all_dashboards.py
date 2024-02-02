from api.dashboards import update_all_dashboards
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Update all the grafana dashboards in the folder"

    def handle(self, *args, **options):
        update_all_dashboards()
