# Activity Log System Documentation

## Overview
The Activity Log system tracks all user activities in the application. Logs are automatically deleted after 10 days to maintain database performance.

## Installation

### 1. Create App Structure
```bash
mkdir -p apps/activity_log
touch apps/activity_log/__init__.py
touch apps/activity_log/apps.py
touch apps/activity_log/models.py
touch apps/activity_log/admin.py
touch apps/activity_log/tasks.py
mkdir -p apps/activity_log/services
touch apps/activity_log/services/__init__.py
touch apps/activity_log/services/logger.py
mkdir -p apps/activity_log/migrations
touch apps/activity_log/migrations/__init__.py
```

### 2. Create `apps.py`
```python
# apps/activity_log/apps.py
from django.apps import AppConfig

class ActivityLogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.activity_log"
    verbose_name = "لاگ فعالیت"
```

### 3. Add to `INSTALLED_APPS`
```python
# config/settings/base.py
INSTALLED_APPS = [
    # ... other apps
    'apps.activity_log.apps.ActivityLogConfig',
]
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Add Celery Beat Schedule
```python
# config/settings/celery.py or config/celery_config.py
CELERY_BEAT_SCHEDULE = {
    # ... other tasks
    'delete-old-activity-logs': {
        'task': 'apps.activity_log.tasks.delete_old_activity_logs',
        'schedule': crontab(hour='2', minute='0'),  # Run daily at 2 AM
    },
    'cleanup-anonymous-logs': {
        'task': 'apps.activity_log.tasks.cleanup_anonymous_logs',
        'schedule': crontab(hour='3', minute='0'),  # Run daily at 3 AM
    },
}
```

### 6. Optional: Add Middleware (for automatic logging)
```python
# config/settings/base.py
MIDDLEWARE = [
    # ... other middleware
    'apps.activity_log.middleware.ActivityLogMiddleware',  # Add at the end
]
```

## Usage Examples

### 1. Basic Logging

```python
from apps.activity_log.models import ActivityLogAction
from apps.activity_log.services.logger import ActivityLogService

# Simple log
ActivityLogService.log(
    user=request.user,
    action=ActivityLogAction.LOGIN,
    description="User logged in successfully"
)
```

### 2. Logging with Request Context

```python
# In a view
def my_view(request):
    # ... your code ...
    
    ActivityLogService.log_from_request(
        request=request,
        action=ActivityLogAction.CREATE,
        description="Created new document"
    )
```

### 3. Logging Authentication

```python
# In authentication views
from apps.activity_log.services.logger import ActivityLogService
from apps.activity_log.models import ActivityLogAction

# Login success
ActivityLogService.log_authentication(
    user=user,
    action=ActivityLogAction.LOGIN,
    request=request,
    is_successful=True
)

# Login failed
ActivityLogService.log_authentication(
    user=user,
    action=ActivityLogAction.LOGIN,
    request=request,
    is_successful=False,
    error_message="Invalid credentials"
)
```

### 4. Logging CRUD Operations

```python
# Create
ActivityLogService.log_crud(
    user=request.user,
    action=ActivityLogAction.CREATE,
    related_object=document,
    request=request
)

# Update
ActivityLogService.log_crud(
    user=request.user,
    action=ActivityLogAction.UPDATE,
    related_object=document,
    request=request,
    metadata={"fields_changed": ["title", "content"]}
)

# Delete
ActivityLogService.log_crud(
    user=request.user,
    action=ActivityLogAction.DELETE,
    related_object=document,
    request=request
)
```

### 5. Logging Payments

```python
# Successful payment
ActivityLogService.log_payment(
    user=request.user,
    action=ActivityLogAction.PAYMENT_SUCCESS,
    amount=50000,
    transaction_id="TX-123456",
    is_successful=True,
    request=request
)

# Failed payment
ActivityLogService.log_payment(
    user=request.user,
    action=ActivityLogAction.PAYMENT_FAILED,
    amount=50000,
    transaction_id="TX-123457",
    is_successful=False,
    request=request,
    error_message="Insufficient funds"
)
```

### 6. Logging AI Chat Activities

```python
ActivityLogService.log_ai_chat(
    user=request.user,
    action=ActivityLogAction.AI_CHAT_STARTED,
    session_id="session-123",
    request=request,
    metadata={
        "chat_type": "v_plus",
        "model": "gpt-4"
    }
)
```

### 7. Custom Logging with Metadata

```python
from apps.activity_log.models import ActivityLogLevel

ActivityLogService.log(
    user=request.user,
    action=ActivityLogAction.EXPORT,
    description="Exported court notifications",
    request=request,
    level=ActivityLogLevel.INFO,
    metadata={
        "format": "PDF",
        "count": 10,
        "date_range": "2025-01-01 to 2025-01-31"
    }
)
```

### 8. Logging Errors

```python
try:
    # Some operation
    do_something()
except Exception as e:
    ActivityLogService.log(
        user=request.user,
        action=ActivityLogAction.OTHER,
        description="Failed to process document",
        request=request,
        level=ActivityLogLevel.ERROR,
        is_successful=False,
        error_message=str(e),
        metadata={
            "document_id": document.pid,
            "error_type": type(e).__name__
        }
    )
```

### 9. Retrieving User Activities

```python
# Get recent activities
recent_activities = ActivityLogService.get_user_activities(
    user=request.user,
    limit=50
)

# Get failed activities
failed_activities = ActivityLogService.get_failed_activities(
    user=request.user,
    limit=20
)

# Filter by action
login_activities = ActivityLogService.get_user_activities(
    user=request.user,
    action=ActivityLogAction.LOGIN,
    limit=10
)
```

## Integration in Views

### ViewSet Example

```python
from rest_framework.viewsets import ModelViewSet
from apps.activity_log.services.logger import ActivityLogService
from apps.activity_log.models import ActivityLogAction

class DocumentViewSet(ModelViewSet):
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        # Log successful creation
        if response.status_code == 201:
            ActivityLogService.log_crud(
                user=request.user,
                action=ActivityLogAction.CREATE,
                related_object=self.get_object(),
                request=request
            )
        
        return response
    
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        
        # Log deletion
        ActivityLogService.log_crud(
            user=request.user,
            action=ActivityLogAction.DELETE,
            related_object=obj,
            request=request
        )
        
        return response
```

### APIView Example

```python
from rest_framework.views import APIView
from rest_framework.response import Response

class ProcessDocumentView(APIView):
    def post(self, request):
        try:
            # Process document
            result = process_document(request.data)
            
            # Log success
            ActivityLogService.log_from_request(
                request=request,
                action=ActivityLogAction.DOCUMENT_ANALYZED,
                description="Document processed successfully",
                metadata={"result": result}
            )
            
            return Response(result)
            
        except Exception as e:
            # Log error
            ActivityLogService.log_from_request(
                request=request,
                action=ActivityLogAction.DOCUMENT_ANALYZED,
                description="Document processing failed",
                is_successful=False,
                error_message=str(e),
                level=ActivityLogLevel.ERROR
            )
            
            raise
```

## Available Actions

Use the predefined actions from `ActivityLogAction`:

- **Authentication**: `LOGIN`, `LOGOUT`, `REGISTER`
- **CRUD**: `CREATE`, `READ`, `UPDATE`, `DELETE`
- **File Operations**: `UPLOAD`, `DOWNLOAD`
- **Payment**: `PAYMENT_INITIATED`, `PAYMENT_SUCCESS`, `PAYMENT_FAILED`
- **Subscription**: `SUBSCRIPTION_PURCHASED`, `SUBSCRIPTION_EXPIRED`
- **AI Chat**: `AI_CHAT_STARTED`, `AI_CHAT_MESSAGE`
- **Document**: `DOCUMENT_ANALYZED`
- **Notification**: `NOTIFICATION_SENT`, `NOTIFICATION_READ`
- **Court**: `COURT_NOTIFICATION_CREATED`, `COURT_CALENDAR_EVENT_CREATED`
- **Wallet**: `WALLET_CHARGE`, `WALLET_DEBIT`
- **Profile**: `PROFILE_UPDATED`, `PASSWORD_CHANGED`
- **Device**: `DEVICE_REGISTERED`, `DEVICE_DEACTIVATED`
- **Other**: `EXPORT`, `IMPORT`, `SEARCH`, `FILTER`, `OTHER`

## Log Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical issues

## Celery Tasks

### Manual Task Execution

```python
# Delete old logs manually
from apps.activity_log.tasks import delete_old_activity_logs
result = delete_old_activity_logs.delay()

# Generate activity report
from apps.activity_log.tasks import generate_activity_report
report = generate_activity_report.delay(user_pid="user-pid-123", days=7)

# Cleanup anonymous logs
from apps.activity_log.tasks import cleanup_anonymous_logs
result = cleanup_anonymous_logs.delay(days=3)
```

## Performance Considerations

1. **Database Indexes**: The model includes indexes on commonly queried fields
2. **Automatic Cleanup**: Logs are deleted after 10 days
3. **Selective Logging**: Don't log every request; be selective
4. **Async Logging**: Consider using Celery tasks for logging in high-traffic scenarios

## Admin Interface

Access the admin interface at `/admin/activity_log/activitylog/` to:
- View all activity logs
- Filter by user, action, level, date
- Search logs by various fields
- View detailed log information

## Best Practices

1. **Log Important Actions**: Focus on business-critical operations
2. **Include Context**: Use metadata for additional context
3. **Use Appropriate Levels**: Use ERROR for failures, INFO for normal operations
4. **Avoid Sensitive Data**: Don't log passwords or sensitive information
5. **Be Consistent**: Use predefined actions consistently
6. **Handle Exceptions**: Always wrap logging in try-except blocks
7. **Use Related Objects**: Link logs to relevant objects for better traceability

## Troubleshooting

### Logs Not Being Deleted

Check if Celery Beat is running:
```bash
celery -A config beat --loglevel=info
```

### Too Many Logs

- Reduce retention period in the task
- Be more selective about what to log
- Consider using log levels to filter less important logs

### Performance Issues

- Ensure indexes are created (run migrations)
- Consider archiving old logs instead of deleting
- Use database query optimization

## Example Integration in Manual Request Upload

```python
# apps/analyzer/api/v1/views/manual_request.py
from apps.activity_log.services.logger import ActivityLogService
from apps.activity_log.models import ActivityLogAction, ActivityLogLevel

class ManualRequestFileUploadViewSet(TainoMobileGenericViewSet):
    
    @action(methods=["POST"], detail=False, url_path="send-documents")
    def upload_documents_email(self, request, **kwargs):
        try:
            self.check_user_balance()
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            result = serializer.save()
            
            # Log successful upload
            ActivityLogService.log(
                user=request.user,
                action=ActivityLogAction.UPLOAD,
                description=f"Uploaded {result['attachments_count']} documents via email",
                request=request,
                metadata={
                    "attachments_count": result['attachments_count'],
                    "service": "manual_request"
                }
            )
            
            return Response(data=result, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            # Log failure
            ActivityLogService.log(
                user=request.user,
                action=ActivityLogAction.UPLOAD,
                description="Failed to upload documents via email",
                request=request,
                level=ActivityLogLevel.ERROR,
                is_successful=False,
                error_message=str(e)
            )
            raise
```

## API Endpoints

### Mobile User Endpoints (v1)

All endpoints require authentication and users can only see their own logs.

#### Base URL: `/api/activity-log/v1/`

1. **GET `/`** - List user's activities
   - Query params: `action`, `level`, `is_successful`, `date_from`, `date_to`, `search`
   - Returns paginated list

2. **GET `/{pid}/`** - Get detailed activity

3. **GET `/stats/`** - Get user's activity statistics (last 7 days)

4. **GET `/failed/`** - Get list of failed activities

5. **GET `/logins/`** - Get recent login activities

6. **GET `/financial/`** - Get financial-related activities

7. **GET `/today-count/`** - Get count of today's activities

### Admin Endpoints

Admins can view all users' activities with advanced filtering.

#### Base URL: `/api/activity-log/admin/`

1. **GET `/`** - List all activities
   - Query params: `user_pid`, `user_phone`, `user_email`, `action`, `level`, `is_successful`, `date_from`, `date_to`, `search`, `has_error`
   - Returns paginated list

2. **GET `/{pid}/`** - Get detailed activity

3. **GET `/system-stats/`** - Get system-wide statistics
   - Query params: `days` (default: 7)

4. **GET `/user-stats/`** - Get statistics for specific user
   - Query params: `user_pid` (required), `days` (default: 7)

5. **GET `/user-summary/`** - Get activity summary for all users

6. **GET `/errors/`** - Get logs with errors

7. **GET `/suspicious/`** - Get suspicious activities (multiple failed attempts)

8. **GET `/by-ip/`** - Get activities by IP address
   - Query params: `ip_address` (required)

9. **GET `/daily-report/`** - Get daily activity report
   - Query params: `date` (YYYY-MM-DD, optional)

10. **POST `/cleanup/`** - Manually trigger log cleanup
    - Query params: `days` (default: 10)

## API Usage Examples

### Mobile User Examples

```text
# Get my recent activities
GET /api/activity-log/v1/?limit=20&ordering=-created_at

# Filter by action
GET /api/activity-log/v1/?action=login

# Get failed activities
GET /api/activity-log/v1/failed/

# Get my statistics
GET /api/activity-log/v1/stats/

# Get today's activity count
GET /api/activity-log/v1/today-count/
```

### Admin Examples

```text
# Get all activities
GET /api/activity-log/admin/?limit=50

# Filter by user
GET /api/activity-log/admin/?user_pid=01j67hzyvysfvns17yjwtnbeqf

# Get system statistics
GET /api/activity-log/admin/system-stats/?days=30

# Get user statistics
GET /api/activity-log/admin/user-stats/?user_pid=01j67hzyvysfvns17yjwtnbeqf&days=7

# Get error logs
GET /api/activity-log/admin/errors/

# Get suspicious activities
GET /api/activity-log/admin/suspicious/

# Get activities by IP
GET /api/activity-log/admin/by-ip/?ip_address=192.168.1.1

# Get daily report
GET /api/activity-log/admin/daily-report/?date=2025-01-15

# Trigger cleanup
POST /api/activity-log/admin/cleanup/?days=10
```

## Response Examples

### Activity List Response
```json
{
  "count": 150,
  "next": "http://api.example.com/api/activity-log/v1/?page=2",
  "previous": null,
  "results": [
    {
      "pid": "01j9abc123...",
      "action": "login",
      "action_display": "ورود",
      "level": "info",
      "level_display": "اطلاعات",
      "description": "User logged in successfully",
      "is_successful": true,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

### Activity Detail Response
```json
{
  "pid": "01j9abc123...",
  "user_info": {
    "pid": "01j67hzy...",
    "phone_number": "9123456789",
    "full_name": "علی احمدی"
  },
  "action": "payment_success",
  "action_display": "پرداخت موفق",
  "level": "info",
  "level_display": "اطلاعات",
  "description": "Payment completed successfully",
  "content_type_name": {
    "app_label": "payment",
    "model": "transaction",
    "name": "transaction"
  },
  "object_id": "01j9def456...",
  "ip_address": "192.168.1.100",
  "endpoint": "/api/payment/v1/verify/",
  "method": "POST",
  "metadata": {
    "amount": 50000,
    "transaction_id": "TX-123456"
  },
  "device_id": "device-abc-123",
  "is_successful": true,
  "error_message": "",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### Stats Response
```json
{
  "total_activities": 245,
  "successful_activities": 230,
  "failed_activities": 15,
  "success_rate": 93.88,
  "action_breakdown": [
    {"action": "login", "count": 50},
    {"action": "create", "count": 40},
    {"action": "update", "count": 35}
  ],
  "level_breakdown": [
    {"level": "info", "count": 200},
    {"level": "warning", "count": 30},
    {"level": "error", "count": 15}
  ],
  "recent_activities": [...]
}
```

## Summary

The Activity Log system provides:
- ✅ Comprehensive activity tracking
- ✅ Automatic cleanup after 10 days
- ✅ Easy-to-use service layer
- ✅ Flexible logging with metadata
- ✅ Admin interface for viewing logs
- ✅ REST APIs for mobile and admin
- ✅ Advanced filtering and statistics
- ✅ Celery tasks for maintenance
- ✅ Performance optimized with indexes
- ✅ Suspicious activity detection
- ✅ User device tracking

Start logging activities in your application to gain insights into user behavior and system usage!
