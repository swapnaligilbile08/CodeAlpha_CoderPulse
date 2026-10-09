from .models import Notification


def unread_count(request):
    """Gives every template `unread_count` for the bell badge."""
    if request.user.is_authenticated:
        return {'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()}
    return {}
