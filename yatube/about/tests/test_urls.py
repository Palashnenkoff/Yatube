from http import HTTPStatus

from django.test import Client, TestCase

# python manage.py test about.tests.test_urls -v 0


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_exist_at_desired_locations(self):
        """
        Проверка доступности страницы 'Об авторе' и 'О технологии' для всех
        """
        urls_status_code = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for url, status in urls_status_code.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_about_urls_uses_correct_templats(self):
        """Проверка шаблонов для страниц 'Об авторе' и 'О технологии'"""
        url_templates_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
