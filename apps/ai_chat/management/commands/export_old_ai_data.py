# apps/ai_chat/management/commands/export_old_ai_data.py
import json
from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
from apps.chat.models import ChatSession, ChatMessage

User = get_user_model()


class Command(BaseCommand):
    help = "Export AI chat data from old chat app to fixture file for ai_chat app"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting export of AI chat data..."))

        # Get all AI chat sessions
        ai_sessions = ChatSession.objects.filter(chat_type="ai", is_deleted=False)

        if not ai_sessions.exists():
            self.stdout.write(self.style.WARNING("No AI chat sessions found to export."))
            return

        fixture_data = []
        session_count = 0
        message_count = 0

        for old_session in ai_sessions:
            session_count += 1

            # Extract AI context data
            ai_context = old_session.ai_context or {}
            ai_type = ai_context.get("ai_type", "v")
            use_coins = ai_context.get("use_coins", True)

            # Create AISession fixture entry
            ai_session_data = {
                "model": "ai_chat.aisession",
                "pk": None,  # Will be auto-assigned
                "fields": {
                    "pid": str(old_session.pid),
                    "user": old_session.client.id,
                    "ai_type": ai_type,
                    "status": old_session.status,
                    "title": old_session.title,
                    "fee_amount": str(old_session.fee_amount),
                    "duration_minutes": old_session.time_limit_minutes or 6,
                    "start_date": old_session.start_date.isoformat() if old_session.start_date else None,
                    "end_time": old_session.end_time.isoformat() if old_session.end_time else None,
                    "ai_context": ai_context,
                    "ai_config": None,  # Will need to be linked after AI configs are imported
                    "paid_with_coins": use_coins,
                    "total_messages": old_session.total_messages,
                    "unread_messages": old_session.unread_client_messages,
                    "creator": old_session.creator.id if old_session.creator else None,
                    "is_active": old_session.is_active,
                    "is_deleted": old_session.is_deleted,
                    "created_at": old_session.created_at.isoformat(),
                    "updated_at": old_session.updated_at.isoformat(),
                },
            }
            fixture_data.append(ai_session_data)

            # Get all messages for this session
            messages = ChatMessage.objects.filter(chat_session=old_session, is_deleted=False)

            for old_message in messages:
                message_count += 1

                # Create AIMessage fixture entry
                ai_message_data = {
                    "model": "ai_chat.aimessage",
                    "pk": None,  # Will be auto-assigned
                    "fields": {
                        "pid": str(old_message.pid),
                        "ai_session_pid": str(old_session.pid),  # Temporary field for reference
                        "sender": old_message.sender.id,
                        "message_type": old_message.message_type,
                        "content": old_message.content,
                        "attachment": old_message.attachment.id if old_message.attachment else None,
                        "is_ai": old_message.is_ai,
                        "is_system": old_message.is_system,
                        "is_read": old_message.is_read_by_client,
                        "read_at": old_message.read_at.isoformat() if old_message.read_at else None,
                        "is_failed": old_message.is_failed,
                        "failure_reason": old_message.failure_reason,
                        "is_active": old_message.is_active,
                        "is_deleted": old_message.is_deleted,
                        "created_at": old_message.created_at.isoformat(),
                        "updated_at": old_message.updated_at.isoformat(),
                    },
                }
                fixture_data.append(ai_message_data)

        # Write to fixture file
        fixture_path = "apps/ai_chat/fixtures/old_ai_chat.json"
        with open(fixture_path, "w", encoding="utf-8") as f:
            json.dump(fixture_data, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully exported:"
                f"\n  - {session_count} AI sessions"
                f"\n  - {message_count} AI messages"
                f"\n  - Total records: {len(fixture_data)}"
                f"\n\nFixture saved to: {fixture_path}"
            )
        )

        self.stdout.write(
            self.style.WARNING(f"\n⚠️  Note: You will need to run the import command to load this data into ai_chat app.")
        )
