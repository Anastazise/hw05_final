from django import forms
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, User, Follow


class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.auth_user = User.objects.create_user(username='TestAuthUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(PostTests.auth_user)
        self.authorized_client_author.force_login(PostTests.author)

    def test_correct_template(self):
        page_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in page_names_templates.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_mainpage_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_text = response.context.get('page_obj')[0].text
        post_author = response.context.get('page_obj')[0].author.username
        group_post = response.context.get('page_obj')[0].group.title
        self.assertEqual(post_text, 'Тестовый пост')
        self.assertEqual(post_author, 'TestAuthor')
        self.assertEqual(group_post, 'Тестовая группа')

    def test_group_list_page_correct_context(self):
        url = reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}
        )
        response = self.authorized_client.get(url)
        group_title = response.context.get('group').title
        group_description = response.context.get('group').description
        group_slug = response.context.get('group').slug
        self.assertEqual(group_title, 'Тестовая группа')
        self.assertEqual(group_description, 'Тестовое описание')
        self.assertEqual(group_slug, 'test_slug')

    def test_profile_page_correct_context(self):
        url = reverse('posts:profile', kwargs={'username': PostTests.author})
        response = self.authorized_client_author.get(url)
        post_text = response.context.get('page_obj')[0].text
        post_author = response.context.get('page_obj')[0].author.username
        group_post = response.context.get('page_obj')[0].group.title
        self.assertEqual(post_text, 'Тестовый пост')
        self.assertEqual(post_author, 'TestAuthor')
        self.assertEqual(group_post, 'Тестовая группа')

    def test_post_detail_pages_correct_context(self):
        url = reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        response = self.authorized_client_author.get(url)
        post_text = response.context.get('post').text
        post_author = response.context.get('post').author.username
        group_post = response.context.get('post').group.title
        self.assertEqual(post_text, 'Тестовый пост')
        self.assertEqual(post_author, 'TestAuthor')
        self.assertEqual(group_post, 'Тестовая группа')

    def test_create_post_edit_correct_context(self):
        url = reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        response = self.authorized_client_author.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        url = reverse('posts:post_create')
        response = self.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_display(self):
        urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}
            ),
        )
        for url in urls:
            response = self.authorized_client_author.get(url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_post_in_right_group(self):
        another_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-another-slug',
            description='Тестовое описание дополнительной группы',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': another_group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_new_comment_created_show_correct_context(self):
        comment_text = f"Комментарий от {self.user_username_value} выводиться"
        form_data = {"text": comment_text}
        response = self.authorized_client.post(
            reverse(
                "posts:add_comment",
                kwargs={"post_id": str(self.post_second.pk)},
            ),
            data=form_data,
            follow=True,
        )
        response = self.client.get(
            reverse(
                "posts:post_detail", kwargs={"post_id": self.post_second.pk}
            )
        )
        context__first_object = response.context["comments"][0]
        self.assertEqual(context__first_object.author, self.user)
        self.assertEqual(context__first_object.text, comment_text)

    def test_cache_index_page(self):
        response = self.client.get(reverse("posts:index"))
        context_first_object_before_add = response.context["page_obj"][0]

        post_text = "Тестовая запись появляется после очистки кэша."
        post = Post.objects.create(
            author=self.user, text=post_text, group=self.group
        )
        response = self.client.get(reverse("posts:index"))
        context_right_after_add = response.context
        self.assertIsNone(context_right_after_add)

        cache.clear()
        response = self.client.get(reverse("posts:index"))
        context_first_object_add_after_clear_cache = response.context[
            "page_obj"
        ][0]
        self.db_vs_context_comparison(
            post, context_first_object_add_after_clear_cache, no_iamge=True
        )

        post.delete()
        response = self.client.get(reverse("posts:index"))
        context_right_after_delete_post = response.context
        self.assertIsNone(context_right_after_delete_post)

        cache.clear()
        response = self.client.get(reverse("posts:index"))
        context_first_object_delete_after_clear_cache = response.context[
            "page_obj"
        ][0]
        self.db_vs_context_comparison(
            context_first_object_before_add,
            context_first_object_delete_after_clear_cache,
            no_iamge=True,
        )

    def test_follow_on_user(self):
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.post_follower.id)
        self.assertEqual(follow.user_id, self.post_autor.id)

    def test_unfollow_on_user(self):
        Follow.objects.create(
            user=self.post_autor,
            author=self.post_follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post_follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_autor)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        post = Post.objects.create(
            author=self.post_autor,
            text="Подпишись на меня")
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
