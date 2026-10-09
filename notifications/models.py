from django.conf import settings
from django.db import models


class Notification(models.Model):
    """Tells `recipient` that `actor` liked, commented on or followed them."""
    KINDS = [
        ('like', 'liked your post'),
        ('comment', 'commented on your post'),
        ('follow', 'started following you'),
    ]
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KINDS)
    post = models.ForeignKey('posts.Post', related_name='+', null=True, blank=True, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.actor} {self.get_kind_display()}'


def notify(recipient, actor, kind, post=None):
    """Create a notification. You never notify yourself."""
    if recipient != actor:
        Notification.objects.create(recipient=recipient, actor=actor, kind=kind, post=post)


def unnotify(recipient, actor, kind, post=None):
    """Remove it again, for example when someone unlikes."""
    Notification.objects.filter(recipient=recipient, actor=actor, kind=kind, post=post).delete()
