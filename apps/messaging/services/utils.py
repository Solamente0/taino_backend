import logging
from typing import Dict, List, Union, Optional, Tuple
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone

from apps.messaging.models import SMSBalance, SMSMessage, SystemSMSTemplate, SMSPurchase

User = get_user_model()
logger = logging.getLogger(__name__)


def format_sms_template(template_code: str, context: Dict[str, str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Format an SMS template with provided context parameters

    Args:
        template_code: The code identifying the template to use
        context: Dictionary of values to substitute in the template

    Returns:
        Tuple containing:
        - Success flag (boolean)
        - Formatted message or None if failed
        - Error message or None if successful
    """
    try:
        # Find the template by code
        template = SystemSMSTemplate.objects.get(code=template_code, is_active=True)

        # Format template with context parameters
        message_content = template.template_content
        for key, value in context.items():
            placeholder = "{" + key + "}"
            message_content = message_content.replace(placeholder, str(value))

        return True, message_content, None

    except SystemSMSTemplate.DoesNotExist:
        error_msg = f"SMS template with code '{template_code}' not found"
        logger.error(error_msg)
        return False, None, error_msg

    except Exception as e:
        error_msg = f"Error formatting SMS template: {str(e)}"
        logger.error(error_msg)
        return False, None, error_msg


@transaction.atomic
def add_sms_balance_to_users(user_ids: List[str], amount: int) -> Dict[str, Union[int, List[Dict]]]:
    """
    Add SMS balance to multiple users in a single transaction

    Args:
        user_ids: List of user IDs to add balance to
        amount: Amount of SMS credits to add to each user

    Returns:
        Dictionary with summary of the operation
    """
    results = []
    success_count = 0

    for user_id in user_ids:
        try:
            user = User.objects.get(pid=user_id)
            balance, created = SMSBalance.objects.get_or_create(user=user)

            # Record previous balance
            previous_balance = balance.balance

            # Add to balance
            balance.add_balance(amount)

            results.append(
                {
                    "user_id": user_id,
                    "user_name": f"{user.first_name} {user.last_name}",
                    "previous_balance": previous_balance,
                    "new_balance": balance.balance,
                    "added": amount,
                    "success": True,
                }
            )

            success_count += 1

        except User.DoesNotExist:
            results.append({"user_id": user_id, "error": "User not found", "success": False})
        except Exception as e:
            results.append({"user_id": user_id, "error": str(e), "success": False})

    return {"total": len(user_ids), "success_count": success_count, "results": results}


def get_sms_statistics(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, user_id: Optional[str] = None
) -> Dict:
    """
    Get comprehensive SMS statistics with optional filtering

    Args:
        start_date: Optional start date for filtering stats
        end_date: Optional end date for filtering stats
        user_id: Optional user ID to get stats for a specific user

    Returns:
        Dictionary with detailed SMS statistics
    """
    # Base query
    messages_query = SMSMessage.objects.all()

    # Apply user filter if provided
    if user_id:
        try:
            user = User.objects.get(pid=user_id)
            messages_query = messages_query.filter(sender=user)
        except User.DoesNotExist:
            return {"error": f"User with ID {user_id} not found", "total_messages": 0}

    # Apply date filters if provided
    if start_date:
        messages_query = messages_query.filter(created_at__gte=start_date)

    if end_date:
        messages_query = messages_query.filter(created_at__lte=end_date)

    # Total messages
    total_messages = messages_query.count()

    # Messages by status
    status_counts = {}
    for status, _ in SMSMessage.STATUS_CHOICES:
        status_counts[status] = messages_query.filter(status=status).count()

    # Messages by source type
    source_type_counts = {}
    for source_type, _ in SMSMessage.SOURCE_TYPE_CHOICES:
        source_type_counts[source_type] = messages_query.filter(source_type=source_type).count()

    # Top users by sent messages
    top_senders = []
    user_counts = (
        messages_query.filter(status="sent").values("sender").annotate(count=models.Count("id")).order_by("-count")[:10]
    )

    for item in user_counts:
        try:
            user = User.objects.get(id=item["sender"])
            top_senders.append({"user_id": user.pid, "name": f"{user.first_name} {user.last_name}", "count": item["count"]})
        except User.DoesNotExist:
            pass

    # Total SMS balance in the system
    total_balance = SMSBalance.objects.aggregate(total=models.Sum("balance"))["total"] or 0

    # Recent purchases
    recent_purchases = []
    purchases = SMSPurchase.objects.all().order_by("-purchase_date")[:10]

    for purchase in purchases:
        recent_purchases.append(
            {
                "user_id": purchase.user.pid,
                "user_name": f"{purchase.user.first_name} {purchase.user.last_name}",
                "coins_spent": purchase.coins_spent,
                "sms_quantity": purchase.sms_quantity,
                "date": purchase.purchase_date,
            }
        )

    # Daily message counts for the past 30 days
    daily_counts = []
    if start_date is None and end_date is None:
        # Default to last 30 days if no date range specified
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

    if start_date and end_date:
        # Get daily counts within the date range
        current_date = start_date.date()
        end_date_normalized = end_date.date()

        while current_date <= end_date_normalized:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())

            day_count = messages_query.filter(created_at__gte=day_start, created_at__lte=day_end).count()

            daily_counts.append({"date": current_date.isoformat(), "count": day_count})

            current_date += timedelta(days=1)

    return {
        "total_messages": total_messages,
        "by_status": status_counts,
        "by_source_type": source_type_counts,
        "top_senders": top_senders,
        "total_balance": total_balance,
        "recent_purchases": recent_purchases,
        "daily_counts": daily_counts,
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    }


def check_low_balance_users(threshold: int = 5) -> List[Dict]:
    """
    Get users with SMS balance below the specified threshold

    Args:
        threshold: Balance threshold to consider as low (default: 5)

    Returns:
        List of dictionaries with user information and balance
    """
    low_balance_users = []

    # Get users with balance below threshold
    balances = SMSBalance.objects.filter(balance__lt=threshold, is_active=True)

    for balance in balances:
        user = balance.user
        low_balance_users.append(
            {
                "user_id": user.pid,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "phone_number": getattr(user, "phone_number", None),
                "balance": balance.balance,
                "last_login": user.last_login,
            }
        )

    return low_balance_users


@transaction.atomic
def send_bulk_sms(
    user_id: str, recipient_numbers: List[str], message: str, client_id: Optional[str] = None, case_id: Optional[str] = None
) -> Dict:
    """
    Send the same SMS message to multiple recipients

    Args:
        user_id: ID of the user sending the messages
        recipient_numbers: List of recipient phone numbers
        message: Message content to send to all recipients
        client_id: Optional client ID to associate with messages
        case_id: Optional case ID to associate with messages

    Returns:
        Dictionary with results of the operation
    """
    from apps.messaging.services.sms_service import SMSService
    from apps.lawyer_office.models import Client, LawOfficeCase

    results = []
    success_count = 0

    try:
        user = User.objects.get(pid=user_id)

        # Resolve related objects if IDs provided
        client = None
        case = None

        if client_id:
            try:
                client = Client.objects.get(pid=client_id)
            except Client.DoesNotExist:
                pass

        if case_id:
            try:
                case = LawOfficeCase.objects.get(pid=case_id)
            except LawOfficeCase.DoesNotExist:
                pass

        # Check if user has enough balance
        balance = SMSService.check_user_sms_balance(user)
        if balance < len(recipient_numbers):
            return {
                "success": False,
                "error": f"Insufficient balance. Required: {len(recipient_numbers)}, Available: {balance}",
                "total": len(recipient_numbers),
                "success_count": 0,
                "results": [],
            }

        # Send to each recipient
        for number in recipient_numbers:
            success, sms_message = SMSService.send_sms(
                user=user, recipient_number=number, message_content=message, client=client, case=case
            )

            if success:
                success_count += 1

            results.append(
                {
                    "recipient": number,
                    "success": success,
                    "status": sms_message.status,
                    "message_id": sms_message.pid,
                    "error": sms_message.error_message if not success else None,
                }
            )

        return {
            "success": True,
            "total": len(recipient_numbers),
            "success_count": success_count,
            "results": results,
            "remaining_balance": SMSService.check_user_sms_balance(user),
        }

    except User.DoesNotExist:
        return {
            "success": False,
            "error": f"User with ID {user_id} not found",
            "total": len(recipient_numbers),
            "success_count": 0,
            "results": [],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total": len(recipient_numbers),
            "success_count": success_count,
            "results": results,
        }


def validate_phone_number(phone_number: str) -> Tuple[bool, Optional[str]]:
    """
    Validate and normalize a phone number for SMS sending

    Args:
        phone_number: Phone number to validate

    Returns:
        Tuple containing:
        - Validation result (boolean)
        - Normalized phone number or error message if invalid
    """
    # Remove any non-digit characters
    cleaned = "".join(filter(str.isdigit, phone_number))

    # Basic validation
    if not cleaned:
        return False, "Phone number contains no digits"

    # Handle Iranian numbers (most common case)
    if cleaned.startswith("98"):
        # Already has country code
        if len(cleaned) == 12:  # 98 + 10 digits
            return True, cleaned
        else:
            return False, "Invalid length for Iranian number with country code"

    # If starts with 0, assume Iranian local format
    if cleaned.startswith("0") and len(cleaned) == 11:  # 0 + 10 digits
        # Ctainoert to international format with 98 country code
        return True, "98" + cleaned[1:]

    # If it's 10 digits, assume Iranian number without prefix
    if len(cleaned) == 10:
        return True, "98" + cleaned

    # Default fallback - return as is if reasonable length
    if 10 <= len(cleaned) <= 15:
        return True, cleaned

    return False, "Phone number has invalid length"


def get_user_sms_summary(user_id: str) -> Dict:
    """
    Get a summary of SMS activity for a specific user

    Args:
        user_id: User ID to get summary for

    Returns:
        Dictionary with user's SMS summary data
    """
    try:
        user = User.objects.get(pid=user_id)

        # Get balance
        balance, created = SMSBalance.objects.get_or_create(user=user)

        # Get message counts
        total_sent = SMSMessage.objects.filter(sender=user, status="sent").count()
        total_failed = SMSMessage.objects.filter(sender=user, status="failed").count()

        # Get purchase history
        purchases = SMSPurchase.objects.filter(user=user).order_by("-purchase_date")[:5]
        recent_purchases = []

        for purchase in purchases:
            recent_purchases.append(
                {"coins_spent": purchase.coins_spent, "sms_quantity": purchase.sms_quantity, "date": purchase.purchase_date}
            )

        # Get recent messages
        recent_messages = SMSMessage.objects.filter(sender=user).order_by("-created_at")[:10]
        messages = []

        for msg in recent_messages:
            messages.append(
                {
                    "recipient": msg.recipient_number,
                    "recipient_name": msg.recipient_name,
                    "status": msg.status,
                    "sent_at": msg.sent_at,
                    "created_at": msg.created_at,
                }
            )

        return {
            "user_id": user.pid,
            "name": f"{user.first_name} {user.last_name}",
            "balance": balance.balance,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "recent_purchases": recent_purchases,
            "recent_messages": messages,
        }

    except User.DoesNotExist:
        return {"error": f"User with ID {user_id} not found"}
