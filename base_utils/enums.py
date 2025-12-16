from enum import Enum

from django.contrib.contenttypes.models import ContentType
from django.db import models


class TainoBaseEnum(Enum):

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def choices(cls):
        return [value for value in cls]


class NamedContentTypeEnum(models.Choices):
    """Anywhere you want to expose content types to api you should not send out content type id
    Instead use this enum class.
    """

    # enum name - enum value: app_label.model - enum label

    # Address app
    ADDRESS = "address.address", "address"

    # Authentication app
    AUTH_PROVIDER = "authentication.authprovider", "auth_provider"
    USER = "authentication.tainouser", "user"
    USER_DOCUMENT = "authentication.userdocument", "user_document"
    USER_TYPE = "authentication.usertype", "user_type"
    USER_PROFILE = "authentication.userprofile", "user_profile"

    # Banner app
    BANNER = "banner.banner", "banner"

    # Chat app
    CHAT_SESSION = "chat.chatsession", "chat_session"
    CHAT_MESSAGE = "chat.chatmessage", "chat_message"
    CHAT_REQUEST = "chat.chatrequest", "chat_request"
    CHAT_SUBSCRIPTION = "chat.chatsubscription", "chat_subscription"
    CHAT_AI_CONFIG = "chat.chataiconfig", "chat_ai_config"

    # Common app
    TERMS_OF_USE = "common.termsofuse", "terms_of_use"
    FAQ = "common.frequentlyaskedquestion", "faq"
    HOME_PAGE = "common.homepage", "home_page"
    SERVICE = "common.service", "service"
    TEAM_MEMBER = "common.teammember", "team_member"
    PARTNERSHIP = "common.partnership", "partnership"
    TESTIMONIAL = "common.testimonial", "testimonial"
    WAY_TO_FILE_TAX = "common.waytofiletax", "way_to_file_tax"
    HERO_SECTION_IMAGE = "common.herosectionimage", "hero_section_image"
    CONTACT_US = "common.contactus", "contact_us"
    NEWSLETTER = "common.newsletter", "newsletter"

    # Country app
    COUNTRY = "country.country", "country"
    STATE = "country.state", "state"
    CITY = "country.city", "city"

    # Court Calendar app
    COURT_CALENDAR_EVENT = "court_calendar.courtcalendarevent", "court_calendar_event"
    COURT_CALENDAR_REMINDER = "court_calendar.courtcalendarreminder", "court_calendar_reminder"
    COURT_CALENDAR_SETTINGS = "court_calendar.courtcalendarsettings", "court_calendar_settings"

    # Court Notification app
    COURT_NOTIFICATION = "court_notification.courtnotification", "court_notification"
    COURT_NOTIFICATION_TEMPLATE = "court_notification.courtnotificationtemplate", "court_notification_template"
    COURT_NOTIFICATION_PREFERENCE = "court_notification.courtnotificationpreference", "court_notification_preference"

    # Document app
    DOCUMENT = "document.tainodocument", "document"

    # Feedback app
    FEEDBACK = "feedback.feedback", "feedback"

    # Lawyer Office app
    LAW_OFFICE = "lawyer_office.lawoffice", "law_office"
    ARCHIVE_CABINET = "lawyer_office.archivecabinet", "archive_cabinet"

    # Social Media app
    SOCIAL_MEDIA_TYPE = "social_media.socialmediatype", "social_media_type"

    # Subscription app
    PACKAGE = "subscription.package", "package"
    USER_SUBSCRIPTION = "subscription.usersubscription", "user_subscription"

    # Wallet app
    WALLET = "wallet.wallet", "wallet"
    TRANSACTION = "wallet.transaction", "transaction"

    @staticmethod
    def get_content_type_by_label(label: str) -> ContentType:
        upper = label.upper()
        attr = getattr(NamedContentTypeEnum, upper, None)
        if attr:
            value = attr.value[0]
            app_label, model_name = value.split(".")
            return ContentType.objects.get(app_label=app_label, model=model_name)

        raise Exception(f"Unknown content type label: {label}")


class GenderTextChoice(models.TextChoices):
    FEMALE = "female", "female"
    MALE = "male", "male"  # Fixed typo: was "female"


class WeekDayChoices(models.IntegerChoices):
    MONDAY = "0", "monday"
    TUESDAY = "1", "tuesday"
    WEDNESDAY = "2", "wednesday"
    THURSDAY = "3", "thursday"
    FRIDAY = "4", "friday"
    SATURDAY = "5", "saturday"
    SUNDAY = "6", "sunday"


class AcceptedVideoMimeType(TainoBaseEnum):
    MP4 = "video/mp4"
    AVI = "video/x-msvideo"
    MOV = "video/quicktime"
    MKV = "video/x-matroska"
    WMV = "video/x-ms-wmv"
    FLV = "video/x-flv"
    WEBM = "video/webm"
    M4V = "video/x-m4v"
    MPG = "video/mpeg"
    MPEG = "video/mpeg"


class AcceptedImageMimeType(TainoBaseEnum):
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    BMP = "image/bmp"
    TIFF = "image/tiff"
    SVG = "image/svg+xml"


class AcceptedDocumentMimeType(TainoBaseEnum):
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DOC = "application/msword"
    TXT = "text/plain"
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    BMP = "image/bmp"
    TIFF = "image/tiff"
    SVG = "image/svg+xml"


class PaymentGatewayType(models.TextChoices):
    ZARINPAL = "zarinpal", "زرین‌پال"
    IDPAY = "idpay", "آیدی پی"
    VANDAR = "vandar", "وندار"
    ZIBAL = "zibal", "زیبال"
    PAYPING = "payping", "پی‌پینگ"
    NEXTPAY = "nextpay", "نکست‌پی"
    OTHER = "other", "سایر"


class LegalDocumentAnalysisType(models.TextChoices):
    LEGAL_DOCUMENT_ANALYSIS = "legal_document_analysis", "تحلیل اسناد حقوقی"
    LEGAL_DOCUMENT_ANALYSIS_AND_DEFENSE = "legal_document_analysis_and_defense", "تحلیل اسناد حقوقی و تنظیم لایحه دفاعی"
    LEGAL_DOCUMENT_ANALYSIS_AND_PRIMARY_PETITION = (
        "legal_document_analysis_and_primary_petition",
        "تحلیل اسناد حقوقی و تنظیم دادخواست بدوی",
    )
    LEGAL_DOCUMENT_ANALYSIS_AND_APPEAL_PETITION = (
        "legal_document_analysis_and_appeal_petition",
        "تحلیل اسناد حقوقی و تنظیم دادخواست تجدید نظر",
    )
    LEGAL_DOCUMENT_ANALYSIS_AND_OBJECTION_PETITION = (
        "legal_document_analysis_and_objection_petition",
        "تحلیل اسناد حقوقی و تنظیم دادخواست واخواهی",
    )
    LEGAL_DOCUMENT_ANALYSIS_AND_PRIMARY_THIRD_PARTY_OBJECTION = (
        "legal_document_analysis_and_primary_third_party_objection",
        "تحلیل اسناد حقوقی و تنظیم اعتراض ثالث اصلی",
    )
    LEGAL_DOCUMENT_ANALYSIS_AND_PROSECUTOR_OBJECTION = (
        "legal_document_analysis_and_prosecutor_objection",
        "تحلیل اسناد حقوقی و اعتراض به قرار دادسرا",
    )

    OTHER = "other", "سایر"

    @staticmethod
    def get_label_for_key(key):
        for l, v in LegalDocumentAnalysisType.choices:
            if l == key:
                return v
        return None  # اگر کلید معتبر نباشد

    @staticmethod
    def get_sanitized_label_for_key(key):
        for l, v in LegalDocumentAnalysisType.choices:
            # print(f"{key=}", flush=True)
            # print(f"{v=}", flush=True)
            # print(f"{v.replace('تحلیل اسناد حقوقی و ', '')=}", flush=True)
            if key == "legal_document_analysis":
                return v
            if l == key:
                return v.replace("تحلیل اسناد حقوقی و ", "")
        return None  # اگر کلید معتبر نباشد
