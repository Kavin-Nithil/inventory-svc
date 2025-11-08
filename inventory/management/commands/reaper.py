import time
import logging
from django.core.management.base import BaseCommand
from inventory.services import InventoryService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run reservation reaper job'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Interval in seconds between runs'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(f'Starting reaper with {interval}s interval...')

        while True:
            try:
                count = InventoryService.reap_expired_reservations()
                if count > 0:
                    self.stdout.write(f'Reaped {count} expired reservations')
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write('Stopping reaper...')
                break
            except Exception as e:
                logger.error(f'Reaper error: {str(e)}')
                time.sleep(interval)