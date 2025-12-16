from django.contrib.auth import get_user_model

from apps.authentication.models import AuthProvider

User = get_user_model()


def set_auth_provider(user: User, code: int) -> AuthProvider | bool:
    try:
        provider = AuthProvider.objects.get(code=code)
        user.auth_provider_id = provider.id
        user.save()
        return provider
    except AuthProvider.DoesNotExist:
        return False
    except Exception as e:
        return False
