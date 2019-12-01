import unittest
from snapshottest import TestCase
import json

from wtos import get_orders

class TestStringMethods(TestCase):

    def test_load_orders(self):
        bc_number = '150'
        posts = load_test_posts()
        orders = get_orders(bc_number, posts)
        self.assertMatchSnapshot(orders)


def load_test_posts():
    with open("posts_150.json") as test_posts:
        return json.loads(test_posts.read())

if __name__ == '__main__':
    unittest.main()
