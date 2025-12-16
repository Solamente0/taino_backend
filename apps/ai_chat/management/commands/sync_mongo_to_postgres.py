# apps/chat/management/commands/sync_mongo_to_postgres.py
import logging
import time
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.ai_chat.services.mongo_sync import MongoSyncService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync chat data from MongoDB to PostgreSQL database"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Run in a continuous loop",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Interval in seconds between syncs (when using --loop)",
        )
    
    def handle(self, *args, **options):
        loop = options.get("loop", False)
        interval = options.get("interval", 60)
        
        if loop:
            self.stdout.write(self.style.SUCCESS(f"Starting continuous sync with interval {interval}s"))
            
            while True:
                try:
                    start = timezone.now()
                    self.stdout.write(f"Starting sync at {start.isoformat()}")
                    
                    MongoSyncService.sync_from_mongo_to_django()
                    
                    end = timezone.now()
                    duration = (end - start).total_seconds()
                    self.stdout.write(self.style.SUCCESS(f"Completed sync in {duration:.2f}s"))
                    
                    time.sleep(interval)
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("Interrupted by user. Exiting..."))
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error in sync: {e}"))
                    time.sleep(interval)
        else:
            try:
                self.stdout.write("Starting one-time sync")
                
                MongoSyncService.sync_from_mongo_to_django()
                
                self.stdout.write(self.style.SUCCESS("Sync completed successfully"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in sync: {e}"))
                raise
