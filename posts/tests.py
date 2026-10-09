import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import Follow, User

from .models import Comment, Like, Post

def png():
    buf = io.BytesIO()
    Image.new('RGB', (4, 4), 'purple').save(buf, 'PNG')
    return SimpleUploadedFile('pic.png', buf.getvalue(), content_type='image/png')

class PostTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', 'a@example.com', 'pw')
        self.b = User.objects.create_user('b', 'b@example.com', 'pw')
        self.client.force_login(self.a)

    def make(self, author=None, **kw):
        data = dict(author=author or self.a, category='tool', title='T', body='B')
        data.update(kw)
        return Post.objects.create(**data)

    def test_create_text_post(self):
        r = self.client.post(reverse('new_post'), {'category': 'tutorial', 'title': 'Hi', 'body': 'Body'})
        post = Post.objects.get()
        self.assertRedirects(r, post.get_absolute_url())
        self.assertEqual(post.author, self.a)

    @override_settings(MEDIA_ROOT='/tmp/coderpulse_test_media')
    def test_create_post_with_image(self):
        self.client.post(reverse('new_post'), {'category': 'tool', 'title': 'Pic', 'body': 'b', 'image': png()})
        self.assertTrue(Post.objects.get().image)

    def test_post_needs_category_title_body(self):
        r = self.client.post(reverse('new_post'), {'title': '', 'body': ''})
        self.assertEqual(Post.objects.count(), 0)
        self.assertContains(r, 'This field is required')

    def test_non_image_upload_rejected(self):
        bad = SimpleUploadedFile('x.png', b'not an image', content_type='image/png')
        self.client.post(reverse('new_post'), {'category': 'tool', 'title': 't', 'body': 'b', 'image': bad})
        self.assertEqual(Post.objects.count(), 0)

    def test_like_and_unlike(self):
        p = self.make(author=self.b)
        r = self.client.post(reverse('like_toggle', args=[p.pk])).json()
        self.assertEqual((r['liked'], r['count']), (True, 1))
        r = self.client.post(reverse('like_toggle', args=[p.pk])).json()
        self.assertEqual((r['liked'], r['count']), (False, 0))
        self.assertEqual(Like.objects.count(), 0)

    def test_like_requires_post_method(self):
        p = self.make()
        self.assertEqual(self.client.get(reverse('like_toggle', args=[p.pk])).status_code, 405)

    def test_comment(self):
        p = self.make()
        self.client.post(reverse('comment_add', args=[p.pk]), {'body': 'Nice!'})
        self.assertEqual(Comment.objects.get().author, self.a)
        self.assertContains(self.client.get(p.get_absolute_url()), 'Nice!')

    def test_empty_comment_ignored(self):
        p = self.make()
        self.client.post(reverse('comment_add', args=[p.pk]), {'body': '   '})
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_html_is_escaped(self):
        p = self.make()
        self.client.post(reverse('comment_add', args=[p.pk]), {'body': '<script>alert(1)</script>'})
        self.assertNotContains(self.client.get(p.get_absolute_url()), '<script>alert(1)</script>')

    def test_counts_are_correct(self):
        p = self.make()
        Like.objects.create(user=self.a, post=p)
        Like.objects.create(user=self.b, post=p)
        for i in range(3):
            Comment.objects.create(post=p, author=self.b, body=str(i))
        got = self.client.get(reverse('home')).context['posts'][0]
        self.assertEqual((got.like_count, got.comment_count, got.liked), (2, 3, True))

    def test_following_feed_only_shows_followed_people(self):
        self.make(title='mine')
        theirs = self.make(author=self.b, title='theirs')
        self.assertEqual(list(self.client.get(reverse('following_feed')).context['posts']), [])
        Follow.objects.create(follower=self.a, following=self.b)
        self.assertEqual(list(self.client.get(reverse('following_feed')).context['posts']), [theirs])

    def test_followers_feed_only_shows_people_who_follow_me(self):
        theirs = self.make(author=self.b, title='theirs')
        self.assertEqual(list(self.client.get(reverse('followers_feed')).context['posts']), [])
        Follow.objects.create(follower=self.b, following=self.a)
        self.assertEqual(list(self.client.get(reverse('followers_feed')).context['posts']), [theirs])
        self.assertEqual(list(self.client.get(reverse('following_feed')).context['posts']), [])

    def test_search_by_text_person_and_category(self):
        self.make(title='Django tips', body='x', category='tutorial')
        self.make(author=self.b, title='Other', body='y', category='tool')
        def titles(**params):
            return {p.title for p in self.client.get(reverse('search'), params).context['posts']}
        self.assertEqual(titles(q='django'), {'Django tips'})
        self.assertEqual(titles(q='b'), {'Other'})
        self.assertEqual(titles(cat='tool'), {'Other'})
        self.assertEqual(titles(), {'Django tips', 'Other'})

    def test_feed_is_newest_first(self):
        for t in ('first', 'second', 'third'):
            self.make(title=t)
        self.assertEqual([p.title for p in self.client.get(reverse('home')).context['posts']], ['third', 'second', 'first'])
