from http import HTTPStatus
from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages(self):
        urls = (
            '/about/author/',
            '/about/tech/',
        )
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        response = self.guest_client.get('/page_404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
