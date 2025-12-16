import logging

from django.conf import settings
from rest_framework import serializers

from apps.document.services.document import DocumentService
from apps.messaging.services.templates import TainoEmailTemplate
from base_utils.enums import NamedContentTypeEnum
from base_utils.serializers.base import TainoBaseSerializer
from base_utils.validators import Validators
from config.settings import AvailableLanguageChoices
import logging

logger = logging.getLogger(__name__)


class ManualRequestEmailDocumentUploadSerializer(TainoBaseSerializer):
    """
    Serializer for sending manual request files via email
    """

    files = serializers.ListField(child=serializers.FileField(), write_only=True)
    # subject = serializers.CharField(required=True)
    message = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_files(self, value):
        logger.info(f"=== Validating {len(value)} files ===")
        for i, file in enumerate(value):
            logger.info(f"=== Validating file {i}: {file.name}, size: {file.size} ===")
            try:
                Validators.validate_uploaded_document_size(file)
                Validators.validate_document(file)
                logger.info(f"=== File {i} validation passed ===")
            except Exception as e:
                logger.error(f"=== File {i} validation failed: {e} ===")
                raise
        return value
    def create(self, validated_data):
        logger.info("=== ENTERING ManualRequestEmailDocumentUploadSerializer.create ===")
        try:
            user = self.context["request"].user
            files = validated_data.get("files", [])
            recipient_email = settings.TAINO_SECRETARY_RECEIPIENT_EMAIL
            logger.info(f"Attempting to send email to: {recipient_email}")
            print(f"Attempting to send email to: {recipient_email}", flush=True)

            # Add these debug logs
            print(f"User: {user}", flush=True)
            print(f"Files count: {len(files)}", flush=True)
            print(f"Recipient email from settings: {recipient_email}", flush=True)

            if not recipient_email:
                print("TAINO_SECRETARY_RECEIPIENT_EMAIL is not set in settings", flush=True)
                raise serializers.ValidationError("Recipient email not configured")

            subject = (
                f"Manual Request Taino User Send documents: User VID: {user.vekalat_id} , User Number: {user.phone_number}"
            )

            message = validated_data.get("message", "")
            description = validated_data.get("description", "")
            body = f"\nپیغام:{message} \n\n\n خواسته کاربر:\n{description}"
            # Use the mail manager to send the email with attachments
            from apps.messaging.services.mail import MailManager
            from django.core.mail import EmailMessage

            # Create an email object
            email = EmailMessage(
                subject=subject,
                body=body,
                to=[recipient_email],
            )

            # Attach each file
            for file in files:
                file.seek(0)  # Reset file pointer
                email.attach(file.name, file.read(), file.content_type)

            # Send the email
            result = email.send()
            logger.info(f"Email send result: {result}")
            print(f"Email send result: {result}", flush=True)

            return {
                "success": True,
                # "message": f"Email sent to {recipient_email} with {len(files)} attachments",
                # "recipient": recipient_email,
                # "subject": subject,
                "attachments_count": len(files),
            }
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            raise serializers.ValidationError(f"Failed to send email: {str(e)}")

    def to_representation(self, instance):
        return instance


class ManualRequestEmailWithTemplateSerializer(ManualRequestEmailDocumentUploadSerializer):
    """
    Serializer for sending manual request documents via email with HTML template
    """

    template_name = serializers.CharField(required=False, default=TainoEmailTemplate.OTP)
    template_context = serializers.DictField(required=False, default=dict)
    language = serializers.ChoiceField(
        choices=[lang.value for lang in AvailableLanguageChoices], default=AvailableLanguageChoices.PERSIAN.value
    )

    def create(self, validated_data):
        user = self.context["request"].user
        files = validated_data.get("files", [])
        recipient_email = settings.TAINO_SECRETARY_RECEIPIENT_EMAIL
        subject = f"AdlIran Taino User Send Documents: User VID: {user.vekalat_id} , User Number: {user.phone_number}"

        template_name = validated_data.get("template_name")
        template_context = validated_data.get("template_context", {})
        language = validated_data.get("language")

        # Render the HTML template
        from apps.messaging.services.templates import TainoEmailTemplateSwitcherService

        template_service = TainoEmailTemplateSwitcherService()

        try:
            rendered_html = template_service.render_template(
                template_name=template_name, language=language, template_context=template_context
            )

            # Send the email with HTML content and attachments
            from apps.messaging.services.mail import MailManager

            mail_manager = MailManager()

            # Create email message
            from django.core.mail import EmailMultiAlternatives

            email = EmailMultiAlternatives(
                subject=subject,
                body="Please view this email in an HTML compatible email client.",
                to=[recipient_email],
            )

            # Attach the HTML version
            email.attach_alternative(rendered_html, "text/html")

            # Attach each file
            for file in files:
                email.attach(file.name, file.read(), file.content_type)

            # Send the email
            email.send()

            return {
                "success": True,
                # "message": f"HTML email sent to {recipient_email} with {len(files)} attachments",
                # "recipient": recipient_email,
                # "subject": subject,
                "template_used": template_name,
                "attachments_count": len(files),
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                # "recipient": recipient_email,
                "subject": subject,
            }


class ManualRequestDocumentUploadSerializer(TainoBaseSerializer):
    """
    Serializer for uploading documents that will be used for court notifications
    """

    creator = serializers.HiddenField(default=serializers.CurrentUserDefault())
    files = serializers.ListField(child=serializers.FileField(), write_only=True)
    file_type = serializers.ChoiceField(
        choices=NamedContentTypeEnum.labels,
        write_only=True,
        default=NamedContentTypeEnum.COURT_NOTIFICATION.label,
    )
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_files(self, value):
        for file in value:
            Validators.validate_uploaded_document_size(file)
            Validators.validate_document(file)
        return value

    def create(self, validated_data):
        file_type = validated_data.get("file_type")
        creator = validated_data.get("creator")
        content_type = NamedContentTypeEnum.get_content_type_by_label(file_type)
        request_files = validated_data.get("files", [])
        description = validated_data.get("description", "")

        # Create documents with uploader as creator
        uploaded_pids = DocumentService().create_documents(
            creator=creator,
            files=request_files,
            content_type=content_type,
        )

        # Return the document PIDs
        return {"document_pids": uploaded_pids, "description": description, "count": len(uploaded_pids)}

    def to_representation(self, instance):
        return instance
