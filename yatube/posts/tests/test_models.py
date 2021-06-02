from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

# python manage.py test posts.tests.test_models

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='пробный текст длинный и очень красивый',
            author=User.objects.create(first_name='Гарри',
                                       last_name='Поттер')
        )
        cls.group = Group.objects.create(
            title='Пробная группа Rammstein',
            slug='ramm',
            description='группа любителей немекой лиркии)))'
        )

    def test_object_name_is_text_field_and_title_field(self):
        post = PostModelTest.post
        group = PostModelTest.group
        object_name = {
            post.text[:15]: post,
            group.title: group, }
        for expected_object_name, model in object_name.items():
            with self.subTest():
                self.assertEquals(expected_object_name, str(model))
