# apps/chat/services/openai_legal_service.py
import logging
import os
from typing import Dict, Optional
from django.core.cache import cache
from openai import OpenAI
import base64
from django.contrib.auth import get_user_model

from apps.ai_chat.models import ChatAIConfig, LegalAnalysisLog

User = get_user_model()
logger = logging.getLogger(__name__)

ASSISTANT_NAME = "Legal Analyst"


class OpenAILegalService:
    """Service for legal document analysis using OpenAI Assistants API"""

    CACHE_EXPIRATION = 60 * 60  # 60 minutes
    ASSISTANT_NAME = "Legal Document Analyzer"

    @staticmethod
    def get_cache_key(user_pid: str) -> str:
        """Generate a cache key for the user's document data"""
        return f"legal_analysis_data:{user_pid}"

    @staticmethod
    def clear_cache(user_pid: str) -> None:
        """Clear the user's document data from cache"""
        cache_key = OpenAILegalService.get_cache_key(user_pid)
        cache.delete(cache_key)

    @staticmethod
    def get_cached_data(user_pid: str) -> Dict:
        """Retrieve user's cached document data"""
        cache_key = OpenAILegalService.get_cache_key(user_pid)
        data = cache.get(cache_key)
        if not data:
            data = {
                "file_ids": [],
                "assistant_id": None,
                "thread_id": None,
                "run_id": None,
                "status": "pending",
                "result": None,
            }
        return data

    @staticmethod
    def update_cache(user_pid: str, data: Dict) -> None:
        """Update the user's document data in cache"""
        cache_key = OpenAILegalService.get_cache_key(user_pid)
        cache.set(cache_key, data, OpenAILegalService.CACHE_EXPIRATION)

    @staticmethod
    def get_ai_config(static_name: str = "v_x") -> Optional[ChatAIConfig]:
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

    @staticmethod
    def get_openai_client():
        """Get authenticated OpenAI client"""
        ai_config = OpenAILegalService.get_ai_config()
        if not ai_config:
            logger.error("No active AI configuration found")
            raise Exception("No active AI configuration found")

        return OpenAI(base_url=ai_config.base_url, api_key=ai_config.api_key)

    @staticmethod
    def upload_file(file_data, file_name):
        """Upload a file to OpenAI and return the file ID"""
        try:
            client = OpenAILegalService.get_openai_client()

            # Create a temporary file to upload
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name

            # Upload the file to OpenAI
            with open(temp_path, "rb") as f:
                response = client.files.create(file=f, purpose="assistants")

            # Clean up temporary file
            os.unlink(temp_path)

            return response.id
        except Exception as e:
            logger.error(f"Error uploading file to OpenAI: {e}")
            raise e

    @staticmethod
    def create_assistant(file_ids):
        """Create or retrieve an assistant for legal document analysis"""
        try:
            client = OpenAILegalService.get_openai_client()
            ai_config = OpenAILegalService.get_ai_config()
            logger.info(f"ai_config  === {ai_config=}")
            logger.info(f"client  === {client=}")

            # Check if the assistant already exists
            assistants_list = client.beta.assistants.list()
            existing = [a for a in assistants_list.data if a.name == ASSISTANT_NAME]
            logger.info(f"existing  === {existing=}")

            # Get system prompt from AI config
            system_prompt = (
                ai_config.system_prompt
                if ai_config and ai_config.system_prompt
                else (
                    "شما یک متخصص حقوقی ایرانی هستید. "
                    "اسناد پیوست شده را بررسی کنید و با استناد به شماره بند و صفحه، "
                    "تحلیل حقوقی دقیقی ارائه دهید. "
                    "لطفاً خلاصه‌ای از پرونده، موضوع اصلی دعوا، ادعاهای طرفین، "
                    "استدلال‌های حقوقی مهم و نتیجه‌ی دادگاه را ارائه دهید. "
                    "همچنین، نقاط قوت و ضعف پرونده را از نظر حقوقی بررسی کنید "
                    "و پیشنهادات حقوقی خود را برای مراحل بعدی ارائه دهید."
                )
            )

            if existing:
                assistant = existing[0]
                # For existing assistants, use the correct API to attach files
                try:
                    existing_files = client.beta.assistant_files.list(assistant_id=assistant.id)
                    existing_file_ids = [f.file_id for f in existing_files.data]
                except Exception as e:
                    existing_file_ids = []
                    logger.error(f"Error adding file to assistant: {e}")

                # Update the assistant's instructions if needed
                client.beta.assistants.update(assistant_id=assistant.id, instructions=system_prompt)

                # Add new files that aren't already attached
                for file_id in file_ids:
                    if file_id not in existing_file_ids:
                        try:
                            client.beta.assistant_files.create(assistant_id=assistant.id, file_id=file_id)
                        except Exception as e:
                            logger.error(f"Error adding file to assistant: {e}")

                return assistant.id
            else:
                logger.info(f"else")

                # Create a new assistant first without files
                assistant = client.beta.assistants.create(
                    name=OpenAILegalService.ASSISTANT_NAME,
                    model=ai_config.model_name,
                    # tools=[{"type": "file_search"}],
                    instructions=system_prompt,
                )
                logger.info(f"assistant.id  === {assistant.id=}")

                # Add files using the correct API endpoint
                for file_id in file_ids:
                    try:
                        client.beta.assistant_files.create(assistant_id=assistant.id, file_id=file_id)
                    except Exception as e:
                        logger.error(f"Error adding file to assistant: {e}")

                return assistant.id

        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            raise e

    @staticmethod
    def create_thread(assistant_id, prompt="", file_ids=None, base64_files=None):
        """Create a thread with the initial prompt and file attachments"""
        try:
            client = OpenAILegalService.get_openai_client()

            # Set default prompt if empty
            if not prompt:
                if file_ids and len(file_ids) > 0:
                    prompt = "لطفا مدارک پیوست شده را تحلیل کنید و یک گزارش جامع حقوقی ارائه دهید."
                else:
                    prompt = "لطفا متن ارائه شده را تحلیل کنید و یک گزارش جامع حقوقی ارائه دهید."

            # Prepare message content array
            message_content = []

            # Add text content
            message_content.append({"type": "text", "text": prompt})

            # Add file attachments by ID if available
            if file_ids:
                for file_id in file_ids:
                    try:
                        # Use file_attachment type instead of image_file for better handling of any file type
                        message_content.append({"type": "file_attachment", "file_id": file_id})
                    except Exception as e:
                        logger.error(f"Error attaching file {file_id} to thread: {e}")

            # Create thread with the message
            thread = client.beta.threads.create(messages=[{"role": "user", "content": message_content}])

            return thread.id

        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            raise e

    @staticmethod
    def run_analysis(assistant_id, thread_id):
        """Run the analysis on the thread"""
        try:
            client = OpenAILegalService.get_openai_client()

            run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=assistant_id)

            return run.id

        except Exception as e:
            logger.error(f"Error running analysis: {e}")
            raise e

    @staticmethod
    def check_run_status(thread_id, run_id):
        """Check the status of the run"""
        try:
            client = OpenAILegalService.get_openai_client()

            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)

            return run.status

        except Exception as e:
            logger.error(f"Error checking run status: {e}")
            raise e

    @staticmethod
    def get_analysis_result(thread_id):
        """Get the result of the analysis"""
        try:
            client = OpenAILegalService.get_openai_client()

            messages = client.beta.threads.messages.list(thread_id=thread_id)

            # Get the latest assistant message
            for message in messages.data:
                if message.role == "assistant":
                    # Extract the text content
                    content = ""
                    for content_item in message.content:
                        if content_item.type == "text":
                            content += content_item.text.value

                    return content

            return "تحلیلی یافت نشد."

        except Exception as e:
            logger.error(f"Error getting analysis result: {e}")
            raise e

    @staticmethod
    def cleanup_files(file_ids):
        """Clean up uploaded files"""
        try:
            client = OpenAILegalService.get_openai_client()

            for file_id in file_ids:
                try:
                    client.files.delete(file_id=file_id)
                except Exception as e:
                    logger.error(f"Error deleting file {file_id}: {e}")

        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
            # Don't raise, just log

    # Update to analyze_documents method in OpenAILegalService

    @staticmethod
    def analyze_documents(user_pid, files_data, prompt="", ai_session_id=None, content_only=False, has_text_content=False):
        """
        Process and start analysis of legal documents

        Args:
            user_pid: User ID for caching
            files_data: Dict of section name to list of file data (binary content)
            prompt: Optional custom prompt or direct content text
            ai_session_id: Optional chat session ID
            content_only: If True, treat prompt as direct content with no files
            has_text_content: Indicates if text content was provided in the sections

        Returns:
            Dict with task status info
        """
        try:
            # Get and clear current data
            user_data = OpenAILegalService.get_cached_data(user_pid)
            user_data["status"] = "processing"
            user_data["file_ids"] = []
            OpenAILegalService.update_cache(user_pid, user_data)

            # If content_only is True, skip file upload and use prompt directly
            if content_only or (has_text_content and not files_data):
                # Create or get assistant without files
                client = OpenAILegalService.get_openai_client()
                ai_config = OpenAILegalService.get_ai_config()

                # Check if the assistant already exists
                assistants_list = client.beta.assistants.list()
                existing = [a for a in assistants_list.data if a.name == ASSISTANT_NAME]

                if existing:
                    assistant_id = existing[0].id
                else:
                    # Create a new assistant
                    assistant = client.beta.assistants.create(
                        name=OpenAILegalService.ASSISTANT_NAME,
                        model=ai_config.model_name,
                        instructions=ai_config.system_prompt,
                    )
                    assistant_id = assistant.id

                # Create thread with prompt only
                thread_id = OpenAILegalService.create_thread(assistant_id, prompt)

                # Start run
                run_id = OpenAILegalService.run_analysis(assistant_id, thread_id)

                # Update cache
                user_data["file_ids"] = []
                user_data["assistant_id"] = assistant_id
                user_data["thread_id"] = thread_id
                user_data["run_id"] = run_id
                user_data["status"] = "running"
                user_data["ai_session_id"] = ai_session_id
                OpenAILegalService.update_cache(user_pid, user_data)

                return {
                    "status": "processing",
                    "assistant_id": assistant_id,
                    "thread_id": thread_id,
                    "run_id": run_id,
                    "file_ids": [],
                    "ai_session_id": ai_session_id,
                    "content_only": True if content_only else False,
                    "has_text_content": has_text_content,
                }

            # Regular flow with file processing
            # Upload all files
            base64_files = []
            file_ids = []
            for section_name, files in files_data.items():
                for i, file_data in enumerate(files):
                    file_name = f"{section_name}_{i}.{file_data['ext']}"

                    # Ctainoert file content to base64
                    file_content = file_data["content"]
                    base64_content = base64.b64encode(file_content).decode("utf-8")

                    # Add to base64_files list with metadata
                    base64_files.append(
                        {
                            "file_name": file_name.lower(),
                            "content_type": f"application/{file_data['ext']}".lower(),
                            "base64_content": base64_content,
                            "extension": file_data["ext"].lower(),
                            "section": section_name,
                        }
                    )

                    # Still upload the file as before
                    file_id = OpenAILegalService.upload_file(file_data["content"], file_name)
                    file_ids.append(file_id)

            # Create or get assistant
            assistant_id = OpenAILegalService.create_assistant(file_ids)

            # Determine if we're using mixed input (files + text)
            is_mixed_input = bool(file_ids) and has_text_content

            # Create thread with prompt
            thread_id = OpenAILegalService.create_thread(assistant_id, prompt, file_ids, base64_files)

            # Start run
            run_id = OpenAILegalService.run_analysis(assistant_id, thread_id)

            # Update cache
            user_data["file_ids"] = file_ids
            user_data["assistant_id"] = assistant_id
            user_data["thread_id"] = thread_id
            user_data["run_id"] = run_id
            user_data["status"] = "running"
            user_data["ai_session_id"] = ai_session_id
            user_data["has_text_content"] = has_text_content
            OpenAILegalService.update_cache(user_pid, user_data)

            return {
                "status": "processing",
                "assistant_id": assistant_id,
                "thread_id": thread_id,
                "run_id": run_id,
                "file_ids": file_ids,
                "ai_session_id": ai_session_id,
                "has_text_content": has_text_content,
            }

        except Exception as e:
            logger.error(f"Error analyzing documents: {e}")

            # Update cache with error
            user_data = OpenAILegalService.get_cached_data(user_pid)
            user_data["status"] = "error"
            user_data["result"] = str(e)
            OpenAILegalService.update_cache(user_pid, user_data)

            return {"status": "error", "error": str(e)}

    @staticmethod
    def check_analysis_status(user_pid):
        """
        Check the status of an analysis

        Args:
            user_pid: User ID for cached data

        Returns:
            Dict with status info
        """
        try:
            user_data = OpenAILegalService.get_cached_data(user_pid)
            is_content_only = "file_ids" in user_data and not user_data["file_ids"]

            if user_data["status"] == "pending":
                return {"status": "pending", "message": "تحلیل هنوز شروع نشده است.", "content_only": is_content_only}

            if user_data["status"] == "error":
                return {"status": "error", "error": user_data.get("result", "خطای نامشخص"), "content_only": is_content_only}

            if user_data["status"] == "completed":
                return {"status": "completed", "analysis": user_data.get("result", ""), "content_only": is_content_only}

            # If running, check current status
            if user_data["run_id"] and user_data["thread_id"]:
                run_status = OpenAILegalService.check_run_status(user_data["thread_id"], user_data["run_id"])

                if run_status in ["completed", "failed", "expired"]:
                    if run_status == "completed":
                        # Get the results
                        result = OpenAILegalService.get_analysis_result(user_data["thread_id"])

                        # Update cache
                        user_data["status"] = "completed"
                        user_data["result"] = result
                        OpenAILegalService.update_cache(user_pid, user_data)

                        # Create or update log record
                        try:
                            user = User.objects.get(pid=user_pid)

                            # Delete previous logs for this user
                            LegalAnalysisLog.objects.filter(user=user).delete()

                            # Create new log
                            ai_session = None
                            if user_data.get("ai_session_id"):
                                from apps.ai_chat.models import AISession

                                try:
                                    ai_session = AISession.objects.get(pid=user_data["ai_session_id"])
                                except AISession.DoesNotExist:
                                    pass

                            LegalAnalysisLog.objects.create(
                                user=user,
                                analysis_text=result,
                                ai_session=ai_session,
                                assistant_id=user_data.get("assistant_id"),
                                thread_id=user_data.get("thread_id"),
                                run_id=user_data.get("run_id"),
                                is_content_only=is_content_only,
                            )
                            logger.info(f"Created legal analysis log for user {user_pid}")
                        except Exception as e:
                            logger.error(f"Error creating legal analysis log: {e}")

                        return {"status": "completed", "analysis": result, "content_only": is_content_only}
                    else:
                        # Error occurred
                        user_data["status"] = "error"
                        user_data["result"] = f"خطا در تحلیل: {run_status}"
                        OpenAILegalService.update_cache(user_pid, user_data)

                        return {"status": "error", "error": f"خطا در تحلیل: {run_status}", "content_only": is_content_only}
                else:
                    # Still processing
                    return {"status": "processing", "message": "در حال تحلیل...", "content_only": is_content_only}

            return {"status": "unknown", "message": "وضعیت تحلیل نامشخص است.", "content_only": is_content_only}

        except Exception as e:
            logger.error(f"Error checking analysis status: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def get_latest_analysis_log(user_pid):
        """
        Get the latest analysis log for a user

        Args:
            user_pid: User ID

        Returns:
            Log object or None
        """
        try:
            user = User.objects.get(pid=user_pid)
            return LegalAnalysisLog.objects.filter(user=user).order_by("-created_at").first()
        except Exception as e:
            logger.error(f"Error getting latest analysis log: {e}")
            return None
