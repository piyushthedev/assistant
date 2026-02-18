import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
import unittest

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data) # Login form title
        self.assertIn(b'Create Account', response.data) # Signup form title (hidden but present)

    def test_login_route_get(self):
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)

    def test_signup_route_get(self):
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 302) # Redirect
        self.assertTrue(response.location.endswith('#signup'))

if __name__ == '__main__':
    unittest.main()
