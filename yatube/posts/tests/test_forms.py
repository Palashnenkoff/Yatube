import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

# python manage.py test posts.tests.test_forms -v 0

User = get_user_model()


class FormTest(TestCase):
    """Проверка формы создания нового поста"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем временную папку для медиа-файлов;
        # на момент теста медиа папка будет переопределена
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

    @classmethod
    def tearDownClass(cls):
        # Модуль shutil - библиотека Python с инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок|файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='Pascha')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='тестовое описание')
        self.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='another_test-slug',
            description='тестовое описание')
        self.post = Post.objects.create(
            text='пробный текст',
            author=self.user,
            group=self.group)
        self.guest_client = Client()

    def test_create_post(self):
        """Валидная форма создает пост и перенаправляет на главную страницу"""
        posts_count = Post.objects.count()
        # Для тестирования загрузки изображений
        # берём байт-последовательность картинки,
        # состоящей из двух пикселей: белого и чёрного
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
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # проверям по полям, что пост создался.
        # [0] так как в мета модели ordering = ['-pub_date']
        post = Post.objects.all()[0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, 'posts/small.gif')
        # Можно еще проверить наличие созданного поста:
        #  т.о assertTrue(Post.objects.filter(.., group=self.group).exists())

    def test_edit_post(self):
        """
        При редактировании поста через форму
        изменяется соответствующая запись в базе данных
        """
        form_data = {
            'text': 'Пробный текст изменен', 'group': self.another_group.id, }
        response = self.authorized_client.post(
            reverse('edit', kwargs={'username': 'Pascha', 'post_id': '1'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={'username': 'Pascha', 'post_id': '1'}))
        self.assertTrue(
            Post.objects.filter(
                text='Пробный текст изменен',
                author=self.user,
                group=self.another_group).exists())
        post = self.post
        response1 = self.authorized_client.get(reverse(
            'group', kwargs={'slug': 'test-slug'}))
        response2 = self.authorized_client.get(reverse(
            'group', kwargs={'slug': 'another_test-slug'}))
        post_count1 = response1.context['page'].count(post)
        post_count2 = response2.context['page'].count(post)
        posts_count = [
            (post_count1, 0, 'Тестовая группа'),
            (post_count2, 1, 'Другая тестовая группа')]
        for posts, count, group in posts_count:
            with self.subTest(group=group):
                self.assertEqual(posts, count)

    def test_guest_client_cant_create_post(self):
        """Неавторизованный пользователь не может публиковать пост"""
        posts_count = Post.objects.count()
        form_data = {'text': 'Не авторизованный текст'}
        response = self.guest_client.post(
            reverse('new_post'), data=form_data, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')
        # проверям, что количество постов не изменилось
        self.assertEqual(Post.objects.count(), posts_count)
