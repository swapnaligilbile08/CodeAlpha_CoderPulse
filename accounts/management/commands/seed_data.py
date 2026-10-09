"""Create 6 fixed demo users, each with 6 posts, plus some follows, likes and comments.

Safe to run on every deploy: it only creates what is missing, so nothing is duplicated.
Render's free plan wipes the SQLite database on each deploy, so build.sh runs this every time.
"""
import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from posts.models import Comment, Like, Post
from accounts.models import Follow

User = get_user_model()

DEMO_PASSWORD = os.environ.get('DJANGO_SEED_PASSWORD', 'Demo@12345')

USERS = [
    ('aarav', 'Aarav', 'Mehta', 'Backend dev. Django, APIs and clean database design.'),
    ('priya', 'Priya', 'Sharma', 'Frontend designer who loves CSS, dark mode and tiny animations.'),
    ('rohan', 'Rohan', 'Verma', 'AI tinkerer. Always trying the newest tools so you do not have to.'),
    ('ananya', 'Ananya', 'Iyer', 'Final-year CS student building one project a month.'),
    ('kabir', 'Kabir', 'Singh', 'Full stack intern. Learning in public.'),
    ('meera', 'Meera', 'Nair', 'Open source contributor and part-time mentor.'),
]

# category keys: tutorial, tool, project, discussion
POSTS = {
    'aarav': [
        ('tutorial', 'Django models in 5 minutes', 'A model is a Python class that becomes a database table. Define fields, run makemigrations, then migrate. That is the whole loop.'),
        ('tutorial', 'Why you should use select_related', 'If you loop over posts and print post.author, Django runs one query per post. select_related("author") joins once and fixes it.'),
        ('discussion', 'SQLite or PostgreSQL for a side project?', 'SQLite is perfect for demos and small apps. Move to PostgreSQL when you need many writers or a persistent hosted database. What do you use?'),
        ('project', 'Idea: a habit tracker API', 'Build a REST API with users, habits and daily check-ins. Add streak counting for a fun challenge.'),
        ('tool', 'Django Debug Toolbar is worth it', 'It shows every SQL query a page runs. You will spot slow pages in seconds.'),
        ('discussion', 'How do you structure Django apps?', 'I keep one app per concept: accounts, posts, notifications. Small apps are easier to test and reuse. Curious how you split yours.'),
    ],
    'priya': [
        ('tutorial', 'Dark mode with CSS variables', 'Define colors as variables on :root, then override them inside a [data-theme="dark"] block. Toggle the attribute with one line of JavaScript.'),
        ('tutorial', 'Flexbox vs Grid, the short version', 'Use Flexbox for one-dimensional rows or columns. Use Grid when you need rows and columns together.'),
        ('tool', 'Figma auto layout changed my workflow', 'Auto layout makes frames resize like real CSS. Designing responsive cards got much faster.'),
        ('project', 'Idea: personal portfolio with a theme switcher', 'Build a one-page portfolio with light and dark themes saved in localStorage. Great first frontend project.'),
        ('discussion', 'Do you design first or code first?', 'I sketch in Figma, then code. It saves rewrites, but some people prototype directly in HTML. What works for you?'),
        ('tool', 'Tiny trick: clamp() for fluid text', 'font-size: clamp(1rem, 2vw, 1.5rem) scales text smoothly without media queries.'),
    ],
    'rohan': [
        ('tool', 'AI code assistants: how I actually use them', 'I use them for boilerplate, tests and explaining unfamiliar code. I still read every line before committing.'),
        ('tool', 'Prompting tip: give examples', 'Showing two input and output examples in a prompt improves results far more than a longer description.'),
        ('project', 'Idea: summarise your notes with an LLM', 'Build a small app that takes pasted notes and returns bullet-point summaries. Add a copy button and you are done.'),
        ('discussion', 'Will AI replace junior developers?', 'I think it changes the work rather than removing it. Understanding fundamentals matters more now. Thoughts?'),
        ('tutorial', 'Calling an API from Python in 4 lines', 'Use the requests library: response = requests.get(url), then response.json(). Check response.status_code first.'),
        ('tool', 'Try a local model for private data', 'Running a small model on your own laptop keeps sensitive text off the internet. Slower, but private.'),
    ],
    'ananya': [
        ('project', 'My project of the month: expense splitter', 'Friends add expenses and the app works out who owes whom. Learned a lot about decimal handling.'),
        ('discussion', 'How do you stay consistent while studying?', 'I code for 45 minutes, then take a 10 minute break. Tracking it in a notebook keeps me honest.'),
        ('tutorial', 'Git basics I wish I knew earlier', 'Commit small and often, write clear messages, and use branches for experiments. git status is your best friend.'),
        ('project', 'Idea: campus event board', 'A site where clubs post events and students RSVP. Add categories and a calendar view.'),
        ('tool', 'VS Code shortcuts that save time', 'Ctrl+D selects the next match, Alt+Up moves a line, and Ctrl+Shift+L edits all matches at once.'),
        ('discussion', 'Is a CS degree enough for jobs?', 'Projects on GitHub seem to matter as much as marks. Share your best advice for freshers.'),
    ],
    'kabir': [
        ('discussion', 'Week 1 of my internship, what I learned', 'Reading the task list carefully saved me hours. Plan first, then code. Learning in public keeps me accountable.'),
        ('tutorial', 'Deploying Django on Render', 'Add a build.sh and Procfile, set your environment variables, and point Render at your GitHub repo. First deploy takes a few minutes.'),
        ('tutorial', 'What does CSRF protection do?', 'It stops other websites from submitting forms as you. Django adds a hidden token to every form to prove the request is yours.'),
        ('project', 'Idea: a mini polling app', 'Users create polls and vote once each. Show live percentages with a bar for each option.'),
        ('tool', 'Postman for testing APIs', 'Save requests in collections and reuse them. Much faster than testing in the browser.'),
        ('discussion', 'Best way to read other people code?', 'I start from the URLs file and follow one request through. What is your method?'),
    ],
    'meera': [
        ('discussion', 'Your first open source contribution', 'Start with documentation fixes or issues labelled good first issue. Small pull requests get merged faster.'),
        ('tutorial', 'Writing a good README', 'Include what it does, a screenshot, how to run it, and how to deploy it. Recruiters often read only this.'),
        ('tool', 'Use pre-commit hooks', 'They run formatters and linters before every commit, so messy code never reaches the repo.'),
        ('project', 'Idea: a code snippet sharing site', 'Users save snippets with tags and syntax highlighting. Add public and private options.'),
        ('discussion', 'Mentoring tip: ask better questions', 'Say what you tried, what you expected, and what happened. Mentors can help you ten times faster.'),
        ('tutorial', 'Testing in Django', 'Write a TestCase, use self.client to hit URLs, and assert on status codes. Run python manage.py test.'),
    ],
}

COMMENTS = [
    'Really useful, thanks for sharing!',
    'Great tip. I am going to try this today.',
    'Totally agree with this.',
    'Nice idea, I might build it.',
    'Good explanation, short and clear.',
]


class Command(BaseCommand):
    help = 'Create 6 demo users with 6 posts each (idempotent).'

    def handle(self, *args, **options):
        now = timezone.now()
        users = {}

        for username, first, last, bio in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first, 'last_name': last, 'bio': bio,
                          'email': f'{username}@example.com'},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users[username] = user

        # Posts: only for users who have none yet, so reruns never duplicate.
        n_posts = 0
        for index, (username, posts) in enumerate(POSTS.items()):
            user = users[username]
            if Post.objects.filter(author=user).exists():
                continue
            for i, (category, title, body) in enumerate(posts):
                post = Post.objects.create(author=user, category=category, title=title, body=body)
                # Spread the dates so the feed looks natural (newest first).
                Post.objects.filter(pk=post.pk).update(
                    created_at=now - timedelta(hours=index * 2 + i * 7 + 1))
                n_posts += 1

        names = list(users.values())

        # Follows: everyone follows the next 3 users in the list.
        for i, user in enumerate(names):
            for step in (1, 2, 3):
                Follow.objects.get_or_create(follower=user, following=names[(i + step) % len(names)])

        # Likes and comments, only when the database has none yet.
        if n_posts and not Like.objects.exists():
            all_posts = list(Post.objects.order_by('pk'))
            for p_index, post in enumerate(all_posts):
                others = [u for u in names if u != post.author]
                for u in others[: (p_index % 4) + 1]:
                    Like.objects.get_or_create(user=u, post=post)
                if p_index % 3 == 0:
                    Comment.objects.create(post=post, author=others[p_index % len(others)],
                                           body=COMMENTS[p_index % len(COMMENTS)])

        self.stdout.write(self.style.SUCCESS(
            f'Seed done: {len(users)} users, {n_posts} new posts. '
            f'Demo password: {DEMO_PASSWORD}'))