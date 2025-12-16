import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional
import docx
from io import BytesIO
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class OCRService:
    """Service to process files with eBoo OCR API"""

    OCR_API_BASE_URL = "https://ocr.taino.ir"
    CACHE_EXPIRATION = 60 * 30  # 30 minutes

    @staticmethod
    def get_cache_key(user_pid: str) -> str:
        """Generate a cache key for the user's OCR data"""
        return f"ocr_data:{user_pid}"

    @staticmethod
    def clear_cache(user_pid: str) -> None:
        """Clear the user's OCR data from cache"""
        cache_key = OCRService.get_cache_key(user_pid)
        cache.delete(cache_key)

    @staticmethod
    def get_cached_data(user_pid: str) -> Dict:
        """Retrieve user's cached OCR data"""
        cache_key = OCRService.get_cache_key(user_pid)
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
        """Update the user's OCR data in cache"""
        cache_key = OCRService.get_cache_key(user_pid)
        cache.set(cache_key, data, OCRService.CACHE_EXPIRATION)

    @staticmethod
    def upload_file(file: UploadedFile) -> Dict:
        """Upload a file to eBoo OCR API"""
        try:
            url = f"{OCRService.OCR_API_BASE_URL}/upload"

            # Reset file pointer to ensure we're reading from the beginning
            file.seek(0)

            # Prepare the file for multipart upload
            # Based on curl example: -F 'file=@IMG_6511.jpg;type=image/jpeg'
            files = {"file": (file.name, file.read(), file.content_type)}

            # Log request details for debugging
            logger.info(f"Uploading file '{file.name}' of type '{file.content_type}' to {url}")

            # Make the request
            response = requests.post(url, files=files)

            # Log response for debugging
            logger.info(f"OCR API Response status: {response.status_code}")
            logger.info(f"OCR API Response content: {response.text[:200]}...")  # Log first 200 chars

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error uploading file to OCR API: {e}")
            logger.error(f"File details: name={file.name}, size={file.size}, type={file.content_type}")
            raise e
        finally:
            file.seek(0)  # Reset file pointer

    @staticmethod
    def ctainoert_file(file_token: str, method: int = 4, output_type: str = "txtrawjson") -> Dict:
        """Ctainoert a file using eBoo OCR API"""
        try:
            url = f"{OCRService.OCR_API_BASE_URL}/ctainoert"
            data = {"file_token": file_token, "method": method, "output_type": output_type}

            logger.info(f"Ctainoerting file with token {file_token} at {url}")
            logger.info(f"Ctainoert request data: {data}")

            response = requests.post(url, data=data)

            # Log response for debugging
            logger.info(f"Ctainoert API Response status: {response.status_code}")
            logger.info(f"Ctainoert API Response content: {response.text[:200]}...")  # Log first 200 chars

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error ctainoerting file with OCR API: {e}")
            raise e

    @staticmethod
    def extract_text_from_docx_url(url: str) -> str:
        """Extract text from a DOCX file URL"""
        try:
            response = requests.get(url)
            response.raise_for_status()

            # Load the docx from the response content
            doc = docx.Document(BytesIO(response.content))

            # Extract text from paragraphs
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])

            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""

    @staticmethod
    def process_file(file: UploadedFile) -> str:
        """Process a file through OCR and return extracted text"""
        try:
            # Step 1: Upload file
            upload_response = OCRService.upload_file(file)
            logger.info(f"Upload response: {upload_response}")

            file_token = upload_response.get("task_id")
            if not file_token:
                logger.error("No file token received from OCR API")
                return ""

            # Step 2: Ctainoert file
            ctainoert_response = OCRService.ctainoert_file(file_token)
            logger.info(f"Ctainoert response: {ctainoert_response}")

            # Step 3: Extract text
            text = ""
            if ctainoert_response.get("success"):
                raw_response = ctainoert_response.get("raw_response", {})
                file_url = raw_response.get("FileToDownload") or ctainoert_response.get("file_to_download")

                if file_url:
                    if file_url.endswith(".docx"):
                        text = OCRService.extract_text_from_docx_url(file_url)
                    else:
                        # Try to get text directly from the response
                        text = ctainoert_response.get("text") or ""

            return text
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            # Return a placeholder to indicate error
            # Don't silently fail as it makes debugging harder
            # Also fixes the issue where the task reports success despite exceptions
            raise e

    @staticmethod
    def add_file_to_section(user_pid: str, section_key: str, file_data: Dict) -> None:
        """Add a processed file to a section in the user's OCR data"""
        user_data = OCRService.get_cached_data(user_pid)

        if section_key not in user_data:
            logger.error(f"Invalid section key: {section_key}")
            return

        user_data[section_key]["files"].append(file_data)
        OCRService.update_cache(user_pid, user_data)

    @staticmethod
    def format_text_for_ai(user_pid: str) -> str:
        """Format all OCR data as text for AI processing"""
        data = OCRService.get_cached_data(user_pid)

        formatted_text = ""

        for section_key, section_data in data.items():
            section_title = section_data["title"]
            files = section_data["files"]

            if not files:
                continue

            formatted_text += f"\n\n{section_title}:\n"

            for file in files:
                formatted_text += f"{file.get('content', '')}\n"

        return formatted_text.strip()
