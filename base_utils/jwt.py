from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.utils import aware_utcnow


def blacklist_all_user_tokens(user):
    """
    Blacklist all refresh tokens belonging to a user.
    This will force the user to login again to get new tokens.
    """
    # Get all outstanding tokens for the user
    outstanding_tokens = OutstandingToken.objects.filter(user_id=user.id)

    # Add all tokens to the blacklist
    for token in outstanding_tokens:
        # Skip tokens that are already blacklisted
        if not BlacklistedToken.objects.filter(token=token).exists():
            BlacklistedToken.objects.create(token=token, blacklisted_at=aware_utcnow())

    return len(outstanding_tokens)
