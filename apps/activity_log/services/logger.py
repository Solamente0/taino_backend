"""
apps/activity_log/services/logger.py
Service for easily logging user activities
"""
import logging
from typing import Optional, Any, Dict

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from apps.activity_log.models import ActivityLog, ActivityLogAction, ActivityLogLevel
from base_utils.services import AbstractBaseService

User = get_user_model()
logger = logging.getLogger(__name__)


class ActivityLogService(AbstractBaseService):
    """
    Service for creating activity logs.
    
    Usage:
        # Simple usage
        ActivityLogService.log(
            user=request.user,
            action=ActivityLogAction.LOGIN,
            description="User logged in successfully"
        )
        
        # With related object
        ActivityLogService.log(
            user=request.user,
            action=ActivityLogAction.CREATE,
            description="Created new document",
            related_object=document,
            request=request
        )
        
        # With metadata
        ActivityLogService.log(
            user=request.user,
            action=ActivityLogAction.PAYMENT_SUCCESS,
            description="Payment completed",
            metadata={"amount": 10000, "transaction_id": "TX123"},
            level=ActivityLogLevel.INFO
        )
    """
    
    @staticmethod
    def log(
        user: Optional[User],
        action: str,
        description: str = "",
        related_object: Optional[Model] = None,
        request: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        metadata: Optional[Dict] = None,
        device_id: Optional[str] = None,
        level: str = ActivityLogLevel.INFO,
        is_successful: bool = True,
        error_message: str = ""
    ) -> Optional[ActivityLog]:
        """
        Create an activity log entry.
        
        Args:
            user: User who performed the action
            action: Action type from ActivityLogAction
            description: Human-readable description
            related_object: Related Django model instance
            request: Django request object (for auto-extracting metadata)
            ip_address: IP address of the user
            user_agent: User agent string
            endpoint: API endpoint
            method: HTTP method
            metadata: Additional JSON data
            device_id: Device identifier
            level: Log level (INFO, WARNING, ERROR, etc.)
            is_successful: Whether the action was successful
            error_message: Error message if action failed
            
        Returns:
            ActivityLog instance or None if creation failed
        """
        try:
            # Extract data from request if provided
            if request:
                if not ip_address:
                    ip_address = ActivityLogService._get_client_ip(request)
                if not user_agent:
                    user_agent = request.META.get('HTTP_USER_AGENT', '')
                if not endpoint:
                    endpoint = request.path
                if not method:
                    method = request.method
                if not device_id:
                    device_id = request.COOKIES.get('device_id', '') or request.META.get('HTTP_X_DEVICE_ID', '')
            
            # Prepare related object data
            content_type = None
            object_id = None
            if related_object:
                content_type = ContentType.objects.get_for_model(related_object)
                object_id = getattr(related_object, 'pid', None) or str(related_object.pk)
            
            # Create log entry
            activity_log = ActivityLog.objects.create(
                user=user,
                action=action,
                level=level,
                description=description,
                content_type=content_type,
                object_id=object_id,
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else "",  # Truncate if too long
                endpoint=endpoint[:500] if endpoint else "",
                method=method,
                metadata=metadata or {},
                device_id=device_id,
                is_successful=is_successful,
                error_message=error_message
            )
            
            return activity_log
            
        except Exception as e:
            logger.error(f"Failed to create activity log: {e}")
            return None
    
    @staticmethod
    def log_from_request(
        request: Any,
        action: str,
        description: str = "",
        related_object: Optional[Model] = None,
        metadata: Optional[Dict] = None,
        level: str = ActivityLogLevel.INFO,
        is_successful: bool = True,
        error_message: str = ""
    ) -> Optional[ActivityLog]:
        """
        Ctainoenience method to log with automatic request data extraction.
        
        Args:
            request: Django request object
            action: Action type
            description: Description
            related_object: Related object
            metadata: Additional data
            level: Log level
            is_successful: Success status
            error_message: Error message
            
        Returns:
            ActivityLog instance or None
        """
        return ActivityLogService.log(
            user=getattr(request, 'user', None),
            action=action,
            description=description,
            related_object=related_object,
            request=request,
            metadata=metadata,
            level=level,
            is_successful=is_successful,
            error_message=error_message
        )
    
    @staticmethod
    def log_authentication(
        user: User,
        action: str,
        request: Optional[Any] = None,
        is_successful: bool = True,
        error_message: str = ""
    ) -> Optional[ActivityLog]:
        """Log authentication-related activities"""
        description = f"کاربر {user.phone_number} {ActivityLogAction(action).label}"
        return ActivityLogService.log(
            user=user,
            action=action,
            description=description,
            request=request,
            level=ActivityLogLevel.INFO if is_successful else ActivityLogLevel.WARNING,
            is_successful=is_successful,
            error_message=error_message
        )
    
    @staticmethod
    def log_crud(
        user: User,
        action: str,
        related_object: Model,
        request: Optional[Any] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[ActivityLog]:
        """Log CRUD operations"""
        model_name = related_object._meta.verbose_name
        descriptions = {
            ActivityLogAction.CREATE: f"ایجاد {model_name}",
            ActivityLogAction.READ: f"مشاهده {model_name}",
            ActivityLogAction.UPDATE: f"ویرایش {model_name}",
            ActivityLogAction.DELETE: f"حذف {model_name}",
        }
        
        return ActivityLogService.log(
            user=user,
            action=action,
            description=descriptions.get(action, f"عملیات {model_name}"),
            related_object=related_object,
            request=request,
            metadata=metadata
        )
    
    @staticmethod
    def log_payment(
        user: User,
        action: str,
        amount: int,
        transaction_id: str,
        is_successful: bool = True,
        request: Optional[Any] = None,
        error_message: str = ""
    ) -> Optional[ActivityLog]:
        """Log payment activities"""
        return ActivityLogService.log(
            user=user,
            action=action,
            description=f"پرداخت {amount} ریال",
            request=request,
            metadata={
                "amount": amount,
                "transaction_id": transaction_id
            },
            level=ActivityLogLevel.INFO if is_successful else ActivityLogLevel.ERROR,
            is_successful=is_successful,
            error_message=error_message
        )
    
    @staticmethod
    def log_ai_chat(
        user: User,
        action: str,
        session_id: str,
        request: Optional[Any] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[ActivityLog]:
        """Log AI chat activities"""
        return ActivityLogService.log(
            user=user,
            action=action,
            description=f"فعالیت چت هوش مصنوعی",
            request=request,
            metadata={
                "session_id": session_id,
                **(metadata or {})
            }
        )
    
    @staticmethod
    def _get_client_ip(request: Any) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    @staticmethod
    def get_user_activities(
        user: User,
        limit: int = 50,
        action: Optional[str] = None,
        level: Optional[str] = None
    ):
        """
        Get recent activities for a user.
        
        Args:
            user: User instance
            limit: Maximum number of logs to return
            action: Filter by action type
            level: Filter by log level
            
        Returns:
            QuerySet of ActivityLog
        """
        queryset = ActivityLog.objects.filter(user=user)
        
        if action:
            queryset = queryset.filter(action=action)
        if level:
            queryset = queryset.filter(level=level)
        
        return queryset[:limit]
    
    @staticmethod
    def get_failed_activities(user: User, limit: int = 50):
        """Get failed activities for a user"""
        return ActivityLog.objects.filter(
            user=user,
            is_successful=False
        ).order_by('-created_at')[:limit]
