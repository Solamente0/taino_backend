# apps/ai_chat/management/commands/import_old_ai_data.py
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from apps.ai_chat.models import AISession, AIMessage, ChatAIConfig

User = get_user_model()


class Command(BaseCommand):
    help = "Import AI chat data from fixture file into ai_chat app"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="apps/ai_chat/fixtures/old_ai_chat.json",
            help="Path to the fixture file (default: apps/ai_chat/fixtures/old_ai_chat.json)",
        )
        parser.add_argument("--clear", action="store_true", help="Clear existing AI chat data before importing")

    def handle(self, *args, **options):
        fixture_path = options["file"]
        clear_existing = options["clear"]

        self.stdout.write(self.style.WARNING(f"Starting import from: {fixture_path}"))

        # Clear existing data if requested
        if clear_existing:
            self.stdout.write(self.style.WARNING("Clearing existing AI chat data..."))
            AIMessage.objects.all().delete()
            AISession.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Cleared existing data"))

        # Load fixture file
        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                fixture_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Fixture file not found: {fixture_path}"))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON in fixture file: {e}"))
            return

        self.stdout.write(f"Found {len(fixture_data)} records to import")

        # Separate sessions and messages
        session_records = [r for r in fixture_data if r["model"] == "ai_chat.aisession"]
        message_records = [r for r in fixture_data if r["model"] == "ai_chat.aimessage"]

        self.stdout.write(f"  - {len(session_records)} AI sessions")
        self.stdout.write(f"  - {len(message_records)} AI messages")

        # Map old PIDs to new session objects
        pid_to_session = {}
        session_count = 0
        message_count = 0
        error_count = 0

        # Import sessions first
        self.stdout.write(self.style.WARNING("\nImporting AI sessions..."))
        for record in session_records:
            fields = record["fields"]
            old_pid = fields["pid"]

            try:
                # Get user
                user = User.objects.get(id=fields["user"])

                # Get creator if exists
                creator = None
                if fields.get("creator"):
                    try:
                        creator = User.objects.get(id=fields["creator"])
                    except User.DoesNotExist:
                        creator = user

                # Get AI config if it exists
                ai_config = None
                if fields.get("ai_type"):
                    ai_config = ChatAIConfig.objects.filter(static_name=fields["ai_type"], is_active=True).first()

                # Check if session already exists
                existing_session = AISession.objects.filter(pid=old_pid).first()
                if existing_session:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  Session {old_pid} already exists, skipping"))
                    pid_to_session[old_pid] = existing_session
                    continue

                # Create new AI session
                ai_session = AISession(
                    pid=old_pid,
                    user=user,
                    ai_type=fields["ai_type"],
                    status=fields["status"],
                    title=fields["title"],
                    fee_amount=fields["fee_amount"],
                    duration_minutes=fields["duration_minutes"],
                    start_date=parse_datetime(fields["start_date"]) if fields["start_date"] else None,
                    end_date=parse_datetime(fields["end_date"]) if fields["end_date"] else None,
                    ai_context=fields.get("ai_context"),
                    ai_config=ai_config,
                    paid_with_coins=fields.get("paid_with_coins", True),
                    total_messages=fields["total_messages"],
                    unread_messages=fields["unread_messages"],
                    creator=creator,
                    is_active=fields["is_active"],
                    is_deleted=fields["is_deleted"],
                )

                # Set timestamps manually
                ai_session.created_at = parse_datetime(fields["created_at"])
                ai_session.updated_at = parse_datetime(fields["updated_at"])

                ai_session.save()

                pid_to_session[old_pid] = ai_session
                session_count += 1

                if session_count % 10 == 0:
                    self.stdout.write(f"  Imported {session_count} sessions...")

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error importing session {old_pid}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✓ Imported {session_count} AI sessions"))

        # Import messages
        self.stdout.write(self.style.WARNING("\nImporting AI messages..."))
        for record in message_records:
            fields = record["fields"]
            old_message_pid = fields["pid"]
            session_pid = fields.get("ai_session_pid")

            try:
                # Get the AI session
                ai_session = pid_to_session.get(session_pid)
                if not ai_session:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️  Session {session_pid} not found for message {old_message_pid}, skipping")
                    )
                    error_count += 1
                    continue

                # Get sender
                sender = User.objects.get(id=fields["sender"])

                # Get attachment if exists
                attachment = None
                if fields.get("attachment"):
                    from apps.document.models import TainoDocument

                    try:
                        attachment = TainoDocument.objects.get(id=fields["attachment"])
                    except TainoDocument.DoesNotExist:
                        pass

                # Check if message already exists
                existing_message = AIMessage.objects.filter(pid=old_message_pid).first()
                if existing_message:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  Message {old_message_pid} already exists, skipping"))
                    continue

                # Create new AI message
                ai_message = AIMessage(
                    pid=old_message_pid,
                    ai_session=ai_session,
                    sender=sender,
                    message_type=fields["message_type"],
                    content=fields["content"],
                    attachment=attachment,
                    is_ai=fields["is_ai"],
                    is_system=fields["is_system"],
                    is_read=fields["is_read"],
                    read_at=parse_datetime(fields["read_at"]) if fields["read_at"] else None,
                    is_failed=fields["is_failed"],
                    failure_reason=fields.get("failure_reason"),
                    is_active=fields["is_active"],
                    is_deleted=fields["is_deleted"],
                )

                # Set timestamps manually
                ai_message.created_at = parse_datetime(fields["created_at"])
                ai_message.updated_at = parse_datetime(fields["updated_at"])

                ai_message.save()

                message_count += 1

                if message_count % 50 == 0:
                    self.stdout.write(f"  Imported {message_count} messages...")

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"  ✗ Error importing message {old_message_pid}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✓ Imported {message_count} AI messages"))

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{"="*60}'
                f"\nImport Summary:"
                f'\n{"="*60}'
                f"\n  ✓ Sessions imported: {session_count}/{len(session_records)}"
                f"\n  ✓ Messages imported: {message_count}/{len(message_records)}"
                f"\n  ✗ Errors: {error_count}"
                f'\n{"="*60}'
            )
        )

        if error_count > 0:
            self.stdout.write(self.style.WARNING(f"\n⚠️  {error_count} records failed to import. Check the errors above."))
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ All records imported successfully!"))
