import unittest
from src.app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_setup_status(self):
        response = self.app.get('/webhook/setup-status')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['is_setup_completed'])

    def test_status(self):
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_sessions', response.json)
        self.assertIn('uptime', response.json)

if __name__ == '__main__':
    unittest.main()