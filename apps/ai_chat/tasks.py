import logging
import base64
import os
import time

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from openai import OpenAI

from apps.ai_chat.models import AISession, LegalAnalysisLog, ChatAIConfig
from apps.ai_chat.services.ai_service import ChatBackendAIService
from apps.ai_chat.services.chat_service import ChatService
from apps.ai_chat.services.ocr_notification import WebSocketNotificationService
from apps.ai_chat.services.ocr_service import OCRService
from apps.ai_chat.services.openai_legal_service import OpenAILegalService

logger = logging.getLogger(__name__)
User = get_user_model()


# @shared_task
# def sync_mongo_to_postgres():
#     """
#     Sync data from MongoDB to PostgreSQL
#     This task should be run periodically
#     """
#     from apps.ai_chat.services.mongo_sync import MongoSyncService
#
#     try:
#         MongoSyncService.sync_from_mongo_to_django()
#         return {"status": "success", "message": "MongoDB sync completed"}
#     except Exception as e:
#         logger.error(f"Error syncing from MongoDB: {e}", exc_info=True)
#         return {"status": "error", "message": str(e)}


@shared_task(bind=True, name="apps.ai_chat.tasks.sync_mongo_to_postgres")
def sync_mongo_to_postgres():
    from django.core.management import call_command

    call_command("sync_mongo_to_postgres")


@shared_task(bind=True, name="apps.ai_chat.tasks.update_expired_ai_sessions")
def update_expired_ai_sessions():
    """
    Periodic task to update expired AI chat sessions
    """
    from django.utils import timezone
    from apps.ai_chat.models import AISession, AISessionStatusEnum
    from apps.ai_chat.services.ai_chat_service import AIChatService

    now = timezone.now()

    expired_sessions = AISession.objects.filter(status=AISessionStatusEnum.ACTIVE, end_date__lt=now, is_deleted=False)

    count = expired_sessions.update(status=AISessionStatusEnum.EXPIRED)

    for session in expired_sessions:
        AIChatService.send_message(
            ai_session=session,
            sender=session.user,
            content="جلسه گفتگو به پایان رسیده است. برای ادامه گفتگو لطفا جلسه جدیدی ایجاد کنید.",
            message_type="system",
            is_system=True,
        )

    return f"Updated {count} expired AI sessions"


@shared_task
def process_ocr_file(user_pid, section_key, file_id, file_title, file_type, file_content_b64):
    """
    Process a single file with OCR and cache the result
    """
    try:
        # Decode base64 content
        file_content = base64.b64decode(file_content_b64)

        # Process the file with OCR service
        from django.core.files.uploadedfile import SimpleUploadedFile

        uploaded_file = SimpleUploadedFile(name=file_title, content=file_content, content_type=file_type)

        extracted_text = OCRService.process_file(uploaded_file)

        # Store the result in the user's cache
        OCRService.add_file_to_section(
            user_pid, section_key, {"id": file_id, "title": file_title, "content": extracted_text, "file_type": file_type}
        )

        return {"success": True, "file_id": file_id, "text_length": len(extracted_text)}

    except Exception as e:
        logger.error(f"Error processing OCR file: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@shared_task
def analyze_ocr_data_with_ai(user_pid, ai_session_id=None):
    """
    Analyze all OCR data for a user with AI
    """
    try:
        # Get all the OCR data from cache
        text_data = OCRService.format_text_for_ai(user_pid)

        if not text_data:
            return {"status": "error", "message": "No OCR data found for analysis"}

        # Get AI configuration
        from apps.ai_chat.services.ai_service import ChatBackendAIService

        ai_config = ChatBackendAIService.get_default_ai_config_sync()

        if not ai_config:
            return {"status": "error", "message": "No AI configuration found"}

        # Prepare prompt for legal analysis
        prompt = (
            "لطفاً این اسناد حقوقی را تحلیل کنید. "
            "خلاصه‌ای از پرونده، موضوع اصلی دعوا، ادعاهای طرفین، "
            "استدلال‌های حقوقی مهم و نتیجه‌ی دادگاه را ارائه دهید. "
            "همچنین، نقاط قوت و ضعف پرونده را از نظر حقوقی بررسی کنید "
            "و پیشنهادات حقوقی خود را برای مراحل بعدی ارائه دهید.\n\n"
            f"{text_data}"
        )

        # Generate analysis with AI
        analysis = ChatBackendAIService.generate_direct_response(prompt, ai_config)

        if not analysis:
            return {"status": "error", "message": "Failed to generate analysis"}

        # If there's a chat session, add the analysis as a message
        if ai_session_id:
            try:
                ai_session = AISession.objects.get(pid=ai_session_id)

                from apps.ai_chat.services.chat_service import ChatService

                ChatService.send_message(
                    ai_session=ai_session,
                    sender=ai_session.client,  # Use client as sender for permissions
                    content=analysis,
                    message_type="text",
                    is_ai=True,
                )

                # Send notification via WebSocket if applicable
                WebSocketNotificationService.send_ocr_analysis_notification(
                    ai_session_id, {"analysis": analysis, "status": "completed"}
                )

            except Exception as e:
                logger.error(f"Error sending analysis to chat: {e}", exc_info=True)

        # Create a log entry for this analysis
        try:
            user = User.objects.get(pid=user_pid)
            ai_session = AISession.objects.get(pid=ai_session_id) if ai_session_id else None

            # First, delete any existing logs for this user
            LegalAnalysisLog.objects.filter(user=user).delete()

            # Create new log
            LegalAnalysisLog.objects.create(user=user, analysis_text=analysis, ai_session=ai_session)
        except Exception as e:
            logger.error(f"Error creating analysis log: {e}", exc_info=True)

        return {"status": "completed", "analysis": analysis}

    except Exception as e:
        logger.error(f"Error analyzing OCR data: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@shared_task
def process_legal_files(user_pid, files_data, prompt="", ai_session_id=None, content_only=False, has_text_content=False):
    """
    Process legal files with OpenAI

    Args:
        user_pid: User ID for caching
        files_data: Dict of section name to list of file data (binary content)
        prompt: Custom prompt or combined text content from sections
        ai_session_id: Optional chat session ID
        content_only: If True, treat prompt as direct content with no files
        has_text_content: Indicates if text content was provided in addition to files
    """
    logger.info(f"plf: {prompt=}")
    logger.info(f"plf: {has_text_content=}")

    try:
        # If content_only is True, we're just using the prompt as content
        if content_only:
            # Start analysis with OpenAI using just the prompt
            result = OpenAILegalService.analyze_documents(
                user_pid=user_pid, files_data={}, prompt=prompt, ai_session_id=ai_session_id, content_only=True
            )

            return result

        # Ctainoert base64 data to binary content
        processed_files = {}
        for section, files in files_data.items():
            processed_files[section] = []
            for file_data in files:
                binary_content = base64.b64decode(file_data["content_b64"])
                ext = file_data["file_name"].split(".")[-1] if "." in file_data["file_name"] else "pdf"
                processed_files[section].append({"content": binary_content, "ext": ext})

        # Start analysis with OpenAI
        result = OpenAILegalService.analyze_documents(
            user_pid=user_pid,
            files_data=processed_files,
            prompt=prompt,
            ai_session_id=ai_session_id,
            has_text_content=has_text_content,
        )

        return result

    except Exception as e:
        logger.error(f"Error processing legal files: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task
def poll_legal_analysis(user_pid, ai_session_id=None, max_attempts=30, interval=10):
    """
    Poll for legal analysis results
    """
    attempts = 0
    is_content_only = False

    # Check if this is a content-only analysis
    user_data = OpenAILegalService.get_cached_data(user_pid)
    if "file_ids" in user_data and not user_data["file_ids"]:
        is_content_only = True

    while attempts < max_attempts:
        try:
            # Check analysis status
            result = OpenAILegalService.check_analysis_status(user_pid)

            # If completed or error, return the result
            if result.get("status") in ["completed", "error"]:
                # If there's a chat session and analysis was successful, add as a message
                if ai_session_id and result.get("status") == "completed":
                    try:
                        ai_session = AISession.objects.get(pid=ai_session_id)
                        analysis = result.get("analysis", "")

                        from apps.ai_chat.services.chat_service import ChatService

                        ChatService.send_message(
                            ai_session=ai_session,
                            sender=ai_session.client,  # Use client as sender for permissions
                            content=analysis,
                            message_type="text",
                            is_ai=True,
                        )

                        # Send notification via WebSocket
                        WebSocketNotificationService.send_ocr_analysis_notification(
                            ai_session_id, {"analysis": analysis, "status": "completed"}
                        )

                    except Exception as e:
                        logger.error(f"Error sending analysis to chat: {e}", exc_info=True)

                # Create a log entry for this analysis
                if result.get("status") == "completed":
                    try:
                        user = User.objects.get(pid=user_pid)
                        ai_session = None
                        if ai_session_id:
                            try:
                                ai_session = AISession.objects.get(pid=ai_session_id)
                            except AISession.DoesNotExist:
                                pass

                        # First, delete any existing logs for this user
                        LegalAnalysisLog.objects.filter(user=user).delete()

                        # Create new log with content_only flag
                        LegalAnalysisLog.objects.create(
                            user=user,
                            analysis_text=result.get("analysis", ""),
                            ai_session=ai_session,
                            assistant_id=user_data.get("assistant_id", ""),
                            thread_id=user_data.get("thread_id", ""),
                            run_id=user_data.get("run_id", ""),
                        )
                    except Exception as e:
                        logger.error(f"Error creating analysis log: {e}", exc_info=True)

                # Add content_only flag to result if applicable
                if is_content_only:
                    result["content_only"] = True

                return result

            # If still processing, wait and try again
            attempts += 1
            time.sleep(interval)

        except Exception as e:
            logger.error(f"Error polling legal analysis: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    # If we've reached max attempts, return a timeout error
    return {"status": "error", "error": "Analysis timed out. Please try again later."}


@shared_task
def analyze_legal_documents_v2x(
    user_pid,
    document_data,
    prompt=None,
    user_request_choice=None,
    ai_session_id=None,
    ai_type=None,
    voice_data=None,  # ✅ ADD THIS
):
    """
    Process legal documents with OpenAI for direct analysis as a background task

    Args:
        user_pid: User's public ID
        document_data: Dictionary containing legal document data
        prompt: Optional custom prompt
        ai_session_id: Optional chat session ID
        user_request_choice: User Request String
        ai_type: User AI Type String

    Returns:
        Dict with analysis results
    """
    try:
        # Get user
        user = User.objects.get(pid=user_pid)

        # Get chat session if provided
        ai_session = None
        if ai_session_id:
            try:
                ai_session = AISession.objects.get(pid=ai_session_id)
            except AISession.DoesNotExist:
                logger.error(f"Chat session with ID {ai_session_id} not found")

        # Initialize section data
        section_persian_names = {
            "initial_petition": "دادخواست بدوی",
            "pleadings": "لوایح طرفین پرونده",
            "first_instance_judgment": "دادنامه بدوی",
            "appeal": "تجدید نظر خواهی",
        }

        # Get AI config
        ai_config = get_ai_config(ai_type)

        temperature = ai_config.temperature or 0.2
        max_tokens = ai_config.max_tokens or 4000

        if not ai_config:
            logger.error("No active AI configuration found")
            return {"status": "error", "message": "No active AI configuration found"}

        # Create OpenAI client
        client = OpenAI(api_key=ai_config.api_key, base_url=ai_config.base_url or "https://api.openai.com/v1")
        second_client = OpenAI(api_key=ai_config.api_key, base_url=ai_config.base_url or "https://api.openai.com/v1")

        # Prepare messages for OpenAI
        # first_messages = []
        second_messages = []

        # Add system prompt
        if ai_config.system_prompt:
            # first_messages.append({"role": "system", "content": ai_config.system_prompt})
            second_messages.append({"role": "system", "content": ai_config.get_combined_system_prompt()})
        else:
            # Default system prompt if none is configured
            backup_system_prompt = {
                "role": "system",
                "content": (
                    "شما یک متخصص حقوقی ایرانی هستید. "
                    "نام شما VX هست و به هیچ عنوان نباید نام دیگری را بگویید. "
                    "اسناد پیوست شده را بررسی کنید و با استناد به شماره بند و صفحه، "
                    "تحلیل حقوقی دقیقی ارائه دهید. "
                    "لطفاً خلاصه‌ای از پرونده، موضوع اصلی دعوا، ادعاهای طرفین، "
                    "استدلال‌های حقوقی مهم و نتیجه‌ی دادگاه را ارائه دهید. "
                    "همچنین، نقاط قوت و ضعف پرونده را از نظر حقوقی بررسی کنید "
                    "و پیشنهادات حقوقی خود را برای مراحل بعدی ارائه دهید."
                ),
            }
            # first_messages.append(backup_system_prompt)
            second_messages.append(backup_system_prompt)
        # Prepare the user message
        # user_first_message = {"role": "user", "content": []}
        # user_first_message["content"].append(
        #     {
        #         "type": "text",
        #         "text": "لطفاً اسناد زیر را از نظر حقوقی تحلیل کنید و یک گزارش جامع ارائه دهید که حداقل 3000 کلمه باشد.",
        #     }
        # )

        user_second_message = {"role": "user", "content": []}
        user_second_message["content"].append({"type": "text", "text": prompt})
        voice_file_path = None
        # ✅ Add voice FIRST if provided
        if voice_data:
            print(f"🎙️ Adding voice to legal analysis: {voice_data['filename']}", flush=True)

            content_type = voice_data.get("content_type", "")
            content_b64 = voice_data.get("content_b64", "")

            data_url = f"data:{content_type};base64,{content_b64}"

            user_second_message["content"].append(
                {"type": "input_audio", "input_audio": {"data": data_url, "format": content_type.split("/")[-1]}}
            )

            print(f"✅ Voice added to legal analysis", flush=True)
        # Extract document sections and their contents
        appeal_data = document_data.get("appeal", {})
        initial_petition_data = document_data.get("initial_petition", {})
        pleadings_data = document_data.get("pleadings", {})
        first_instance_judgment_data = document_data.get("first_instance_judgment", {})

        appeal_files = appeal_data.get("files", [])
        initial_petition_files = initial_petition_data.get("files", [])
        pleadings_files = pleadings_data.get("files", [])
        first_instance_judgment_files = first_instance_judgment_data.get("files", [])

        # Add content from all files to the user message
        for section_key, files_list in [
            ("appeal", appeal_files),
            ("initial_petition", initial_petition_files),
            ("pleadings", pleadings_files),
            ("first_instance_judgment", first_instance_judgment_files),
        ]:
            if not files_list:
                continue

            for file in files_list:
                content = file.get("content", "")
                # file_title = section_persian_names[section_key]
                file_title = ""
                # user_first_message["content"].append({"type": "text", "text": f"\n\n--- {file_title} ---\n\n{content}"})
                user_second_message["content"].append({"type": "text", "text": f"\n\n--- {file_title} ---\n\n{content}"})
        # Add the user message to messages
        # first_messages.append(user_first_message)
        second_messages.append(user_second_message)
        # logger.info(f"cstomeee messag::: {first_messages}")
        logger.info(f"sec cstomee messag::: {second_messages}")
        # Call OpenAI API for analysis
        # response = client.chat.completions.create(
        #     model=ai_config.model_name,
        #     messages=first_messages,
        #     temperature=temperature,  # Lower temperature for more focused response
        #     max_tokens=max_tokens,  # Allow for detailed analysis
        # )

        # Extract the analysis from the response
        # analysis = response.choices[0].message.content.strip()

        second_response = second_client.chat.completions.create(
            model=ai_config.model_name,
            messages=second_messages,
            temperature=temperature,  # Lower temperature for more focused response
            max_tokens=max_tokens,  # Allow for detailed analysis
        )
        user_request_analysis = second_response.choices[0].message.content.strip()
        # If we have a chat session, save the analysis as a message
        if ai_session:
            ChatService.send_message(
                ai_session=ai_session,
                sender=ai_session.client,  # Use client as sender for permissions
                # content=analysis,
                content=user_request_analysis,
                message_type="text",
                is_ai=True,
            )

        # Save the analysis to the database for future reference
        try:
            # Delete previous logs for this user to avoid clutter
            LegalAnalysisLog.objects.filter(user=user, ai_type=ai_type).delete()

            # Create new log
            LegalAnalysisLog.objects.create(
                user=user,
                # analysis_text=analysis,
                analysis_text=None,
                user_request_analysis_text=user_request_analysis,
                user_request_choice=user_request_choice,
                ai_type=ai_type,
                ai_session=ai_session,
                is_content_only=len(appeal_files) == 0,
            )

        except Exception as e:
            logger.error(f"Error saving analysis log: {e}")
            # Cleanup on error

        return {
            "status": "success",
            "analysis_result": {
                # "analysis": analysis,
                "analysis": None,
                "user_request_analysis": user_request_analysis,
                "user_request_choice": user_request_choice,
            },
        }

    except Exception as e:
        logger.error(f"Error analyzing documents: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def get_ai_config(static_name: str = "v_x"):
    """Get AI configuration for OpenAI interaction"""
    try:
        # First, try to get the config with the specified static_name
        config = ChatAIConfig.objects.filter(static_name=static_name, is_active=True).first()
        if not config:
            # Fall back to default config
            config = ChatAIConfig.objects.filter(is_default=True, is_active=True).first()
        return config
    except Exception as e:
        logger.error(f"Error getting AI config: {e}")
        return None
