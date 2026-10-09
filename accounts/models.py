from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Count, Exists, OuterRef
from django.urls import reverse

from .validators import MaxFileSize


class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    bio = models.TextField(max_length=280, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, validators=[MaxFileSize(5)])

    @property
    def display_name(self):
        return self.get_full_name().strip()

    @property
    def initials(self):
        return self.username[:2].upper()

    def get_absolute_url(self):
        return reverse('profile', args=[self.username])

    @property
    def followers_count(self):
        return self.follower_set.count()

    @property
    def following_count(self):
        return self.following_set.count()

    def suggestions(self, limit=5):
        """People you don't follow yet, most followed first. `follows_me` says if they follow you."""
        return (User.objects.exclude(pk=self.pk).exclude(follower_set__follower=self)
                .annotate(n_followers=Count('follower_set'),
                          follows_me=Exists(Follow.objects.filter(follower=OuterRef('pk'), following=self)))
                .order_by('-n_followers', '-pk')[:limit])


class Follow(models.Model):
    """One row means `follower` follows `following`."""
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following_set', on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='follower_set', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower} -> {self.following}'
