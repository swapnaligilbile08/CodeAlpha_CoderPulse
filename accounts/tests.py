from django.test import TestCase
from django.urls import reverse

from .models import Follow, User

class AuthTests(TestCase):
    def test_register_logs_you_in(self):
        r = self.client.post(reverse('register'), {
            'username': 'newbie', 'email': 'n@example.com',
            'password1': 'Str0ng-Pass-77', 'password2': 'Str0ng-Pass-77'})
        self.assertRedirects(r, reverse('home'))
        self.assertTrue(User.objects.filter(username='newbie').exists())

    def test_duplicate_email_rejected(self):
        User.objects.create_user('a', 'same@example.com', 'pw')
        r = self.client.post(reverse('register'), {
            'username': 'b', 'email': 'SAME@example.com',
            'password1': 'Str0ng-Pass-77', 'password2': 'Str0ng-Pass-77'})
        self.assertContains(r, 'already exists')

    def test_login_and_logout(self):
        User.objects.create_user('a', 'a@example.com', 'Str0ng-Pass-77')
        r = self.client.post(reverse('login'), {'username': 'a', 'password': 'Str0ng-Pass-77'})
        self.assertRedirects(r, reverse('home'))
        self.client.post(reverse('logout'))
        self.assertRedirects(self.client.get(reverse('home')), '/login/?next=/home/')

    def test_pages_need_login(self):
        for name in ('home', 'search', 'new_post', 'following_feed', 'followers_feed', 'settings'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302, name)

class ProfileAndFollowTests(TestCase):
    def setUp(self):
        self.a = User.objects.create_user('a', 'a@example.com', 'pw')
        self.b = User.objects.create_user('b', 'b@example.com', 'pw')
        self.client.force_login(self.a)

    def test_edit_profile(self):
        self.client.post(reverse('edit_profile'), {'first_name': 'Ann', 'last_name': 'Lee', 'bio': 'hi'})
        self.a.refresh_from_db()
        self.assertEqual((self.a.display_name, self.a.bio), ('Ann Lee', 'hi'))

    def test_follow_then_unfollow(self):
        r = self.client.post(reverse('follow_toggle', args=['b'])).json()
        self.assertEqual((r['following'], r['followers']), (True, 1))
        self.assertEqual(self.a.following_count, 1)
        r = self.client.post(reverse('follow_toggle', args=['b'])).json()
        self.assertEqual((r['following'], r['followers']), (False, 0))

    def test_cannot_follow_yourself(self):
        self.assertEqual(self.client.post(reverse('follow_toggle', args=['a'])).status_code, 400)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follower_lists(self):
        Follow.objects.create(follower=self.a, following=self.b)
        self.assertEqual([u.username for u in self.client.get(reverse('followers', args=['b'])).context['users']], ['a'])
        self.assertEqual([u.username for u in self.client.get(reverse('following', args=['a'])).context['users']], ['b'])

    def test_follow_button_state_in_lists(self):
        c = User.objects.create_user('c', 'c@example.com', 'pw')
        d = User.objects.create_user('d', 'd@example.com', 'pw')
        Follow.objects.create(follower=c, following=self.b)
        Follow.objects.create(follower=d, following=self.b)
        Follow.objects.create(follower=self.a, following=c)
        users = {u.username: u.i_follow for u in self.client.get(reverse('followers', args=['b'])).context['users']}
        self.assertEqual(users, {'c': True, 'd': False})

    def test_list_pages_have_followers_following_switch(self):
        r = self.client.get(reverse('followers', args=['b']))
        self.assertContains(r, reverse('followers', args=['b']))
        self.assertContains(r, reverse('following', args=['b']))

    def test_suggestions_skip_me_and_people_i_follow(self):
        c = User.objects.create_user('c', 'c@example.com', 'pw')
        d = User.objects.create_user('d', 'd@example.com', 'pw')
        Follow.objects.create(follower=self.a, following=self.b)
        Follow.objects.create(follower=d, following=c)
        Follow.objects.create(follower=c, following=self.a)
        got = list(self.a.suggestions())
        self.assertEqual([u.username for u in got], ['c', 'd'])
        self.assertEqual([u.follows_me for u in got], [True, False])

    def test_home_shows_suggestions_column(self):
        User.objects.create_user('c', 'c@example.com', 'pw')
        r = self.client.get(reverse('home'))
        self.assertContains(r, 'Suggestions for you')
        self.assertContains(r, 'class="tab tab-bell side-only')

    def test_profile_has_posts_followers_following_switch(self):
        Follow.objects.create(follower=self.b, following=self.a)
        r = self.client.get(reverse('profile', args=['a']))
        self.assertContains(r, reverse('followers', args=['a']))
        self.assertContains(r, reverse('following', args=['a']))
        self.assertContains(r, 'data-followers-count')

    def test_list_pages_do_not_carry_the_live_followers_count(self):
        self.assertNotContains(self.client.get(reverse('followers', args=['a'])), 'data-followers-count')

    def test_profile_tab_stays_lit_on_my_own_lists_only(self):
        mine = self.client.get(reverse('following', args=['a'])).content.decode()
        theirs = self.client.get(reverse('following', args=['b'])).content.decode()
        lit = lambda html: 'class="tab active" aria-label="Profile"' in html
        self.assertTrue(lit(mine))
        self.assertFalse(lit(theirs))

class AuthPageTests(TestCase):
    def test_login_page_holds_both_forms_with_unique_ids(self):
        r = self.client.get(reverse('login'))
        self.assertContains(r, 'id="login_username"')
        self.assertContains(r, 'id="register_username"')
        self.assertNotContains(r, 'auth-box active')

    def test_register_page_opens_on_the_register_side(self):
        self.assertContains(self.client.get(reverse('register')), 'auth-box active')

    def test_wrong_password_stays_on_login_side(self):
        User.objects.create_user('a', 'a@example.com', 'Str0ng-Pass-77')
        r = self.client.post(reverse('login'), {'username': 'a', 'password': 'nope'})
        self.assertContains(r, 'role="alert"')
        self.assertNotContains(r, 'auth-box active')

    def test_bad_sign_up_stays_on_register_side(self):
        r = self.client.post(reverse('register'), {'username': 'x', 'email': 'bad', 'password1': 'a', 'password2': 'b'})
        self.assertContains(r, 'auth-box active')
        self.assertContains(r, 'errorlist')

    def test_password_may_match_username(self):
        r = self.client.post(reverse('register'), {'username': 'ramverma', 'email': 'r@example.com',
                                                   'password1': 'ramverma', 'password2': 'ramverma'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(username='ramverma').exists())
