import shutil
import tempfile

import datetime as dt

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Follow

# python manage.py test posts.tests.test_views -v 0

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.MEDIA_ROOT))
class TemplateTest(TestCase):
    """Проверяет соответсие шаблонов адресам"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='тестовый текст'
        )

        cls.post = Post.objects.create(
            text='пробный текст',
            pub_date=dt.datetime.now(),
            author=User.objects.create_user(username='Pascha'),
            group=TemplateTest.group,
            image=uploaded)

        cls.another_group = Group.objects.create(
            title='Другая группа',
            slug='test-slug-another',
            description='Группа без постов')

    @classmethod
    def tearDownClass(cls):
        # Модуль shutil - библиотека Python с инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок|файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='Гарри')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # авторизуем автора поста
        self.author_client = Client()
        self.author_client.force_login(TemplateTest.post.author)

    def post_context(self, context, flag_post):
        """Отдельный метод, проверяющий контекс поста"""
        # #метод используется на страницах, где отображен пост
        post = TemplateTest.post
        if flag_post:
            value = context['post']
        else:
            value = context['page'][0]
        self.assertEqual(value.text, post.text)
        self.assertEqual(value.group, post.group)
        self.assertEqual(value.author, post.author)
        self.assertEqual(value.pub_date.date(), dt.date.today())
        self.assertEqual(value.image, 'posts/small.gif')

    def test_pages_use_correct_template(self):
        """View функции используют соответствующие шаблоны."""
        templates_pages_names = {
            # 'index.html': reverse('index'),
            'group.html': reverse('group', args={TemplateTest.group.slug}),
            'new_post.html': reverse('new_post'),
            'profile.html': reverse('profile', args={
                TemplateTest.post.author.username}),
            'follow.html': reverse('follow_index'), }
        # Проверяем, что при обращении к name вызывается
        # соответствующий HTML-шаблон
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Добавлено после ревью: тест, что при редактировании поста
    #  атором используется шаблон new_post
    def test_post_edits_pages_use_correct_template(self):
        response = self.author_client.get(reverse('edit', kwargs={
            'username': TemplateTest.post.author.username,
            'post_id': TemplateTest.post.id}))
        self.assertTemplateUsed(response, 'new_post.html')

    def test_home_page_shows_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        # #используем метод проверки поста
        self.post_context(response.context, False)

    def test_group_posts_page_shows_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', args={TemplateTest.group.slug}))
        self.post_context(response.context, False)
        self.assertEqual(
            response.context['group'].title, TemplateTest.group.title)
        self.assertEqual(response.context['group'].description, (
            TemplateTest.group.description))
        self.assertEqual(
            response.context['group'].slug, TemplateTest.group.slug)

    def test_newpost_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_edit_page_shows_correct_context(self):
        """Шаблон new_post edit сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('edit', kwargs={
            'username': TemplateTest.post.author.username,
            'post_id': TemplateTest.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        # проверяем, что в поле text есть текст
        self.assertContains(response, TemplateTest.post.text)

    def test_profile_page_shows_correct_context(self):
        """Шаблон страницы пользователя сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'profile', kwargs={'username': TemplateTest.post.author.username}))
        self.post_context(response.context, False)
        # проверяем, что передается имя пользователя
        self.assertEqual(
            response.context['author'].username,
            TemplateTest.post.author.username)
        # проверяем, что передается кол-во постов
        self.assertEqual(TemplateTest.post.author.posts.count(), 1)

    def test_post_page_shows_correct_context(self):
        """Шаблон отдельного поста сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'post', kwargs={
                'username': TemplateTest.post.author.username,
                'post_id': TemplateTest.post.id}))
        self.assertEqual(
            response.context['author'].username,
            TemplateTest.post.author.username)
        self.assertEqual(TemplateTest.post.author.posts.count(), 1)
        self.post_context(response.context, True)

    def test_new_post_exist_in_definit_group_and_homepage(self):
        """
        Проверяет что, пост есть только
        на галвной странице и на странице своей группы
        """
        post = TemplateTest.post
        response_1 = self.authorized_client.get(reverse('index'))
        response_2 = self.authorized_client.get(
            reverse('group', args={TemplateTest.group.slug}))
        response_3 = self.authorized_client.get(
            reverse('group', kwargs={'slug': TemplateTest.another_group.slug}))
        post_count_1 = response_1.context['page'].count(post)
        post_count_2 = response_2.context['page'].count(post)
        post_count_3 = response_3.context['page'].count(post)
        response_count = [
            (post_count_1, 1, 'name1'),
            (post_count_2, 1, 'name2'),
            (post_count_3, 0, 'name3')
        ]
        for post_count, count_expected, name in response_count:
            with self.subTest(name=name):
                self.assertEqual(post_count, count_expected)

    def test_pagiator(self):
        """ Проверяет, что на страницы выводится не более 10 постов"""
        Post.objects.bulk_create([
            Post(
                text='еще 13 текстов',
                pub_date=dt.datetime.now(),
                author=TemplateTest.post.author,
                group=TemplateTest.group)
            for post in range(13)
        ])
        response_index = self.author_client.get(reverse(
            'index'))
        response_group = self.author_client.get(reverse(
            'group', kwargs={'slug': TemplateTest.group.slug}))
        response_profile = self.author_client.get(reverse(
            'profile', kwargs={'username': TemplateTest.post.author.username}))
        posts_on_page_index = len(response_index.context['page'])
        posts_on_page_group = len(response_group.context['page'])
        posts_on_page_profile = len(response_profile.context['page'])
        posts_count = [
            (posts_on_page_index, 10),
            (posts_on_page_group, 10),
            (posts_on_page_profile, 10)
        ]
        for posts, count in posts_count:
            with self.subTest(posts=posts):
                self.assertEqual(posts, count)

    def test_authorized_client_can_follow_author(self):
        """
        Проверяет возможность подписки/отписки на автора зареганым
        пользователем и невохзможность подписаться на самого себя
        """
        # при подписке создается модель
        author = TemplateTest.post.author.username
        self.authorized_client.get(reverse('profile_follow', args={author}))
        is_follow = Follow.objects.filter(
            user=self.user, author=TemplateTest.post.author).exists()
        self.assertTrue(is_follow)
        # при отписке модель стирается
        self.authorized_client.get(reverse('profile_unfollow', args={author}))
        is_follow = Follow.objects.filter(
            user=self.user, author=TemplateTest.post.author).exists()
        self.assertFalse(is_follow)
        # пользователь не может подписаться сам на себя
        self.author_client.get(reverse('profile_follow', args={author}))
        is_follow = Follow.objects.filter(
            user=TemplateTest.post.author,
            author=TemplateTest.post.author).exists()
        self.assertFalse(is_follow)

    def test_one_following(self):
        """Можно подписаться на пользователя только один раз"""
        author = TemplateTest.post.author
        for x in range(2):
            self.authorized_client.get(reverse(
                'profile_follow', args={author}
            ))
        followings = Follow.objects.filter(user=self.user, author=author)
        self.assertEqual(followings.count(), 1)

    def test_posts_for_followers(self):
        """
        Проверяет, что новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него.
        """
        author = TemplateTest.post.author
        # подписываем первого пользователя на автора
        self.authorized_client.get(reverse('profile_follow',
                                           args={author.username}))
        # создаем второго авторизованного пользователя
        self.user2 = User.objects.create_user(username='Рон')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        # проверям количество постов по подписке
        response1 = self.authorized_client.get(reverse('follow_index'))
        response2 = self.authorized_client2.get(reverse('follow_index'))
        posts_count1 = len(response1.context['page'])
        posts_count2 = len(response2.context['page'])
        posts_count = {
            (posts_count1, 1, 'Подписанный пользователь'),
            (posts_count2, 0, 'Неподписанный пользователь')
        }
        for posts, count, user in posts_count:
            with self.subTest(user=user):
                self.assertEqual(posts, count)
        # # проверяет, что text=='текст для подписчиков' у последнего
        # поста :self.assertEqual(response.context['page'][0].text, post.text)
