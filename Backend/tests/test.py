import unittest
from app import app

class FlaskAppTests(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_home_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Connected MongoDB Successfully', response.data)

if __name__ == '__main__':
    unittest.main()