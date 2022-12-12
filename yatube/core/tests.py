from django.test import TestCase


class ViewTestClass(TestCase):
    def test_404_page(self):
        response = self.client.get('/nonexist-page/')
        template = 'core/404.html'
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, template)
