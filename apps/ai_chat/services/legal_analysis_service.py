import logging
import base64
import tempfile
import os
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from openai import OpenAI

from apps.ai_chat.models import ChatAIConfig

logger = logging.getLogger(__name__)


class LegalAnalysisService:
    """Service to process legal documents with OpenAI GPT for direct analysis"""

    CACHE_EXPIRATION = 60 * 30  # 30 minutes

    @staticmethod
    def get_cache_key(user_pid: str) -> str:
        """Generate a cache key for the user's document data"""
        return f"legal_analysis_data:{user_pid}"

    @staticmethod
    def clear_cache(user_pid: str) -> None:
        """Clear the user's document data from cache"""
        cache_key = LegalAnalysisService.get_cache_key(user_pid)
        cache.delete(cache_key)

    @staticmethod
    def get_cached_data(user_pid: str) -> Dict:
        """Retrieve user's cached document data"""
        cache_key = LegalAnalysisService.get_cache_key(user_pid)
        data = cache.get(cache_key)
        if not data:
            data = {
                "Initial_Petition": {"title": "دادخواست بدوی", "files": []},
                "Pleadings_of_the_Parties": {"title": "لوایح طرفین پرونده", "files": []},
                "First_Instance_Judgment": {"title": "دادنامه بدوی", "files": []},
                "Appeal": {"title": "تجدید نظر خواهی", "files": []},
            }
        return data

    @staticmethod
    def update_cache(user_pid: str, data: Dict) -> None:
        """Update the user's document data in cache"""
        cache_key = LegalAnalysisService.get_cache_key(user_pid)
        cache.set(cache_key, data, LegalAnalysisService.CACHE_EXPIRATION)

    @staticmethod
    def get_ai_config(static_name: str = "v_x") -> Optional[ChatAIConfig]:
        """Get AI configuration for ChatGPT interaction"""
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
    def add_file_to_section(user_pid: str, section_key: str, file_data: Dict) -> None:
        """Add a file reference to a section in the user's document data"""
        user_data = LegalAnalysisService.get_cached_data(user_pid)

        if section_key not in user_data:
            logger.error(f"Invalid section key: {section_key}")
            return

        user_data[section_key]["files"].append(file_data)
        LegalAnalysisService.update_cache(user_pid, user_data)

    @staticmethod
    def analyze_legal_documents(user_pid: str, files_data: Dict[str, List[UploadedFile]]) -> str:
        """
        Analyze legal documents directly using ChatGPT

        Args:
            user_pid: User's public ID for caching
            files_data: Dictionary mapping section keys to lists of uploaded files

        Returns:
            The analysis results as text
        """
        try:
            # Get AI config
            ai_config = LegalAnalysisService.get_ai_config()
            if not ai_config:
                logger.error("No active AI configuration found")
                return "خطا: تنظیمات هوش مصنوعی یافت نشد."

            # Create OpenAI client
            client = OpenAI(api_key=ai_config.api_key)

            # Prepare messages with system prompt and all document files
            messages = [
                {
                    "role": "system",
                    "content": "شما یک متخصص تحلیل حقوقی هستید. وظیفه شما بررسی و تحلیل حقوقی اسناد پرونده ارسالی است. خلاصه‌ای از پرونده، موضوع اصلی دعوا، ادعاهای طرفین، استدلال‌های حقوقی مهم و نتیجه‌ی دادگاه را ارائه دهید. همچنین، نقاط قوت و ضعف پرونده را از نظر حقوقی بررسی کنید و پیشنهادات حقوقی خود را برای مراحل بعدی ارائه دهید.",
                }
            ]

            # Add user message with instructions
            user_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": "لطفاً اسناد زیر را از نظر حقوقی تحلیل کنید و یک گزارش جامع ارائه دهید:"}
                ],
            }

            # Add all files to the user message
            for section_key, files_list in files_data.items():
                if not files_list:
                    continue

                # Add section header
                user_message["content"].append({"type": "text", "text": f"\n\n--- {section_key} ---\n"})

                # Add all files in this section
                for file in files_list:
                    file.seek(0)  # Ensure we're at the start of the file
                    file_content = file.read()

                    # Determine content type for appropriate handling
                    content_type = getattr(file, "content_type", "application/octet-stream")

                    # For images and PDFs, add as image_url
                    if content_type.startswith("image/") or content_type == "application/pdf":
                        user_message["content"].append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type};base64,{base64.b64encode(file_content).decode('utf-8')}"
                                },
                            }
                        )
                    # For text files, try to add as text
                    elif content_type == "text/plain":
                        try:
                            text_content = file_content.decode("utf-8")
                            user_message["content"].append({"type": "text", "text": text_content})
                        except UnicodeDecodeError:
                            # If decoding fails, treat as binary and add note
                            user_message["content"].append(
                                {"type": "text", "text": f"(فایل متنی غیرقابل خواندن: {file.name})"}
                            )
                    # For other files, add a note
                    else:
                        user_message["content"].append(
                            {"type": "text", "text": f"(فایل با فرمت {content_type} نمی‌تواند مستقیم پردازش شود: {file.name})"}
                        )

                    # Store file info in cache
                    file_data = {
                        "title": file.name,
                        "file_type": content_type,
                        "id": f"file_{section_key}_{len(user_data[section_key]['files']) + 1}",
                    }

                    # Add to cache
                    user_data = LegalAnalysisService.get_cached_data(user_pid)
                    user_data[section_key]["files"].append(file_data)
                    LegalAnalysisService.update_cache(user_pid, user_data)

            # Add the user message to the messages list
            messages.append(user_message)

            # Call the API for analysis
            response = client.chat.completions.create(
                model=ai_config.model_name,
                messages=messages,
                temperature=ai_config.temperature,
                max_tokens=ai_config.max_tokens,
            )

            analysis = response.choices[0].message.content.strip()
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing documents: {e}", exc_info=True)
            return f"خطا در تحلیل اسناد: {str(e)}"

    @staticmethod
    def analyze_documents_from_cache(user_pid: str) -> str:
        """Analyze the stored document info for a user using ChatGPT"""
        try:
            # Get user data from cache
            user_data = LegalAnalysisService.get_cached_data(user_pid)

            # Check if we have any files
            has_files = False
            for section_key, section_data in user_data.items():
                if section_data.get("files"):
                    has_files = True
                    break

            if not has_files:
                return "داده‌ای برای تحلیل یافت نشد. لطفاً اسناد را مجدداً آپلود کنید."

            # Get AI config
            ai_config = LegalAnalysisService.get_ai_config()
            if not ai_config:
                logger.error("No active AI configuration found")
                return "خطا: تنظیمات هوش مصنوعی یافت نشد."

            # Create summary text of what files were uploaded
            document_summary = "فایل‌های آپلود شده:\n\n"
            for section_key, section_data in user_data.items():
                if not section_data.get("files"):
                    continue

                document_summary += f"{section_data['title']}:\n"
                for file in section_data.get("files", []):
                    document_summary += f"- {file.get('title', 'بدون عنوان')} ({file.get('file_type', 'نامشخص')})\n"
                document_summary += "\n"

            # Create prompt for analysis
            prompt = f"""
            تحلیل حقوقی مدارک پرونده:

            با توجه به مدارک آپلود شده توسط کاربر، خلاصه‌ای از پرونده، موضوع اصلی دعوا، ادعاهای طرفین، 
            استدلال‌های حقوقی مهم و نتیجه‌ی دادگاه را ارائه دهید. همچنین، نقاط قوت و ضعف پرونده را 
            از نظر حقوقی بررسی کنید و پیشنهادات حقوقی خود را برای مراحل بعدی ارائه دهید.

            {document_summary}
            """

            # Create OpenAI client and call API
            client = OpenAI(api_key=ai_config.api_key)

            response = client.chat.completions.create(
                model=ai_config.model_name,
                messages=[{"role": "system", "content": ai_config.system_prompt}, {"role": "user", "content": prompt}],
                temperature=ai_config.temperature,
                max_tokens=ai_config.max_tokens,
            )

            analysis = response.choices[0].message.content.strip()
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing documents from cache: {e}", exc_info=True)
            return f"خطا در تحلیل اسناد: {str(e)}"
