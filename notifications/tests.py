from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from posts.models import Post

from .models import Notification

class NotificationTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', 'a@example.com', 'pw')
        self.b = User.objects.create_user('b', 'b@example.com', 'pw')
        self.post = Post.objects.create(author=self.a, category='tool', title='Hello', body='x')
        self.client.force_login(self.b)

    def test_like_notifies_author_and_unlike_removes_it(self):
        self.client.post(reverse('like_toggle', args=[self.post.pk]))
        n = Notification.objects.get()
        self.assertEqual((n.recipient, n.actor, n.kind, n.post), (self.a, self.b, 'like', self.post))
        self.client.post(reverse('like_toggle', args=[self.post.pk]))
        self.assertEqual(Notification.objects.count(), 0)

    def test_comment_notifies_author(self):
        self.client.post(reverse('comment_add', args=[self.post.pk]), {'body': 'Nice'})
        self.assertEqual(Notification.objects.get().kind, 'comment')

    def test_follow_notifies_and_unfollow_removes(self):
        self.client.post(reverse('follow_toggle', args=['a']))
        self.assertEqual(Notification.objects.get().kind, 'follow')
        self.client.post(reverse('follow_toggle', args=['a']))
        self.assertEqual(Notification.objects.count(), 0)

    def test_no_notification_for_your_own_actions(self):
        self.client.force_login(self.a)
        self.client.post(reverse('like_toggle', args=[self.post.pk]))
        self.client.post(reverse('comment_add', args=[self.post.pk]), {'body': 'me'})
        self.assertEqual(Notification.objects.count(), 0)

    def test_page_shows_unread_then_marks_all_read(self):
        self.client.post(reverse('like_toggle', args=[self.post.pk]))
        self.client.force_login(self.a)
        self.assertContains(self.client.get(reverse('home')), 'bell-count')
        r = self.client.get(reverse('notifications'))
        self.assertContains(r, 'b</b> liked your post')
        self.assertContains(r, 'unread')
        self.assertNotContains(self.client.get(reverse('home')), 'bell-count')
        self.assertNotContains(self.client.get(reverse('notifications')), 'notif glass unread')

    def test_you_only_see_your_own(self):
        self.client.post(reverse('like_toggle', args=[self.post.pk]))
        self.assertContains(self.client.get(reverse('notifications')), 'No notifications yet')

    def test_page_needs_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('notifications')).status_code, 302)
