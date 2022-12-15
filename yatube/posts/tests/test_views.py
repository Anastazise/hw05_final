import shutil
import tempfile
from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post
from yatube.settings import POSTS_PER_PAGE
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00'
    b'\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)
uploaded = SimpleUploadedFile(
    name='small.gif',
    content=small_gif,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.author = User.objects.create_user(
            username='auth'
        )
        cls.authorized_author_client = Client()
        cls.authorized_author_client.force_login(cls.author)
        cls.not_author = User.objects.create_user(
            username='test_not_author'
        )
        cls.authorized_not_author_client = Client()
        cls.authorized_not_author_client.force_login(cls.not_author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description'
        )

        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author,
            image=uploaded,
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_context(self, response_post):
        self.assertEqual(response_post.author, self.post.author)
        self.assertEqual(response_post.group, self.group)
        self.assertEqual(response_post.text, self.post.text)
        self.assertEqual(response_post.image, self.post.image)

    def test_index_shows_correct_context(self):
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.check_context(response.context['page_obj'][0])

    def test_profile_shows_correct_context(self):
        response = self.authorized_not_author_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}))
        self.assertEqual(response.context['author'], self.user)
        self.check_post_info(response.context['page_obj'][0])

    def test_post_detail_shows_correct_context(self):
        response = self.authorized_not_author_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}))
        self.check_post_info(response.context['post'])

    def test_group_post_shows_correct_context(self):
        response = self.authorized_not_author_client.get(
            reverse('posts:group_list', args=[self.group.slug]))
        response_group = response.context.get('group')
        response_post = response.context['page_obj'][0]
        self.check_context(response_post)
        self.assertEqual(self.author, response_post.author)
        self.assertEqual(self.group.title, response_group.title)
        self.assertEqual(self.group.description, response_group.description)
        self.assertEqual(self.group.slug, response_group.slug)

    def test_post_create_and_post_edit_show_correct_context(self):
        urls_pages = [reverse('posts:post_create'),
                      reverse('posts:post_edit', args=[self.post.id])]
        for url in urls_pages:
            response = self.authorized_author_client.get(url)
            for value, expected in self.form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_pages_show_new_post(self):
        group = Group.objects.create(
            title='some_title',
            slug='some_slug',
            description='some_description'
        )
        form_data = {
            'text': 'some_text',
            'group': group.pk,
        }
        response_create = self.authorized_not_author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response_create_post = response_create.context.get('post')
        URLS = [reverse('posts:index'), reverse('posts:profile',
                args=[self.author.username]),
                reverse('posts:group_list', args=[self.group.slug])]
        responses = []
        for url in URLS:
            response = self.authorized_not_author_client.get(url)
        responses.append(response)
        response_posts = []
        for response in responses:
            response_post = response.context.get('post')
        response_posts.append(response_post)
        self.assertIn(response_create_post, response_posts)

    def test_new_post_do_not_view_other_group(self):
        second_test_slug = 'second-test-group'
        Group.objects.create(
            title='other title',
            slug=second_test_slug,
            description='other description',
        )
        response = self.authorized_not_author_client.get(
            reverse('posts:group_list', args=[second_test_slug]))
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text='some_text',
                group=cls.group,
                author=cls.author
            )

        cls.templates = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[cls.group.slug]),
            reverse('posts:profile', args=[cls.author.username]),
        ]

    def test_first_page_contains_ten_records(self):
        for template in self.templates:
            with self.subTest(template=template):
                response = self.client.get(template)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_PER_PAGE)

    def test_second_page_contains_three_records(self):
        for template in self.templates:
            with self.subTest(template=template):
                response = self.client.get((template) + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 len(range(13)) - POSTS_PER_PAGE)
