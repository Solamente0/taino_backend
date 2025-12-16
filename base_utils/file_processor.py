import logging
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class FileProcessorService:
    """سرویس پردازش فایل‌ها برای ارسال به AI"""

    # فرمت‌های مجاز
    ALLOWED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "webp", "gif"}
    ALLOWED_DOCUMENT_FORMATS = {"pdf"}

    @staticmethod
    def count_pdf_pages(file: UploadedFile) -> int:
        """
        شمارش تعداد صفحات PDF با PyMuPDF (سریع و کارآمد)

        Args:
            file: فایل آپلود شده

        Returns:
            تعداد صفحات
        """
        try:
            # خواندن محتوای فایل
            file.seek(0)
            file_content = file.read()
            file.seek(0)  # بازگشت به ابتدای فایل

            # باز کردن PDF با PyMuPDF
            doc = fitz.open(stream=file_content, filetype="pdf")
            page_count = doc.page_count
            doc.close()

            logger.info(f"PDF page count: {page_count}")
            return page_count

        except Exception as e:
            logger.error(f"Error counting PDF pages: {e}")
            raise ValueError(f"خطا در پردازش فایل PDF: {str(e)}")

    @staticmethod
    @staticmethod
    def validate_image(file: UploadedFile) -> Tuple[bool, Optional[str]]:
        """اعتبارسنجی فایل تصویر"""
        try:
            file.seek(0)
            img = Image.open(file)

            # بررسی فرمت
            format_lower = img.format.lower() if img.format else ""
            if format_lower not in FileProcessorService.ALLOWED_IMAGE_FORMATS:
                return False, f"فرمت تصویر باید یکی از {', '.join(FileProcessorService.ALLOWED_IMAGE_FORMATS)} باشد"

            # بررسی حجم (حداکثر 100MB) ← INCREASED
            file.seek(0, 2)
            size_mb = file.tell() / (1024 * 1024)
            if size_mb > 100:  # ← Changed from 20
                return False, "حجم تصویر نباید بیشتر از 100 مگابایت باشد"

            file.seek(0)
            return True, None

        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return False, f"خطا در اعتبارسنجی تصویر: {str(e)}"

    @staticmethod
    def validate_pdf(file: UploadedFile, max_pages: int = 50) -> Tuple[bool, Optional[str], int]:
        """اعتبارسنجی فایل PDF"""
        try:
            # بررسی حجم (حداکثر 200MB) ← INCREASED
            file.seek(0, 2)
            size_mb = file.tell() / (1024 * 1024)
            file.seek(0)

            if size_mb > 200:  # ← Changed from 50
                return False, "حجم PDF نباید بیشتر از 200 مگابایت باشد", 0

            # شمارش صفحات
            page_count = FileProcessorService.count_pdf_pages(file)

            if page_count > max_pages:
                return False, f"تعداد صفحات PDF نباید بیشتر از {max_pages} باشد", page_count

            return True, None, page_count

        except Exception as e:
            logger.error(f"Error validating PDF: {e}")
            return False, f"خطا در اعتبارسنجی PDF: {str(e)}", 0

    @staticmethod
    def prepare_file_for_api(file: UploadedFile, file_type: str) -> dict:
        """
        آماده‌سازی فایل برای ارسال به API

        Args:
            file: فایل آپلود شده
            file_type: نوع فایل (image یا document)

        Returns:
            دیکشنری حاوی اطلاعات فایل برای API
        """
        try:
            file.seek(0)

            if file_type == "image":
                # برای تصاویر، از base64 استفاده می‌کنیم
                import base64

                image_data = base64.b64encode(file.read()).decode("utf-8")

                # تشخیص mime type
                img = Image.open(BytesIO(base64.b64decode(image_data)))
                mime_type = f"image/{img.format.lower()}"

                return {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}}

            elif file_type == "document":
                # برای PDF نیز از base64 استفاده می‌کنیم
                import base64

                pdf_data = base64.b64encode(file.read()).decode("utf-8")

                return {
                    "type": "image_url",  # OpenRouter از همین فرمت برای PDF هم استفاده می‌کند
                    "image_url": {"url": f"data:application/pdf;base64,{pdf_data}"},
                }

            else:
                raise ValueError(f"نوع فایل نامعتبر: {file_type}")

        except Exception as e:
            logger.error(f"Error preparing file for API: {e}")
            raise ValueError(f"خطا در آماده‌سازی فایل: {str(e)}")

    @staticmethod
    def get_file_type(file: UploadedFile) -> Optional[str]:
        """
        تشخیص نوع فایل

        Returns:
            'image', 'document' یا None
        """
        try:
            filename = file.name.lower()

            if any(filename.endswith(f".{ext}") for ext in FileProcessorService.ALLOWED_IMAGE_FORMATS):
                return "image"
            elif filename.endswith(".pdf"):
                return "document"

            return None

        except Exception as e:
            logger.error(f"Error detecting file type: {e}")
            return None
