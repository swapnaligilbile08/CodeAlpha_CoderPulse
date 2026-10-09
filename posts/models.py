from django.conf import settings
from django.db import models
from django.urls import reverse

from accounts.validators import MaxFileSize

CATEGORIES = [
    ('tutorial', 'Tutorial'),
    ('tool', 'Tool/AI Update'),
    ('project', 'Project Idea'),
    ('discussion', 'Discussion'),
]
CATEGORY_KEYS = [key for key, _ in CATEGORIES]


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='posts', on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    title = models.CharField(max_length=140)
    body = models.TextField(max_length=5000)
    image = models.ImageField(upload_to='posts/', blank=True, validators=[MaxFileSize(10)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.pk])


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comments', on_delete=models.CASCADE)
    body = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='likes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'post')
