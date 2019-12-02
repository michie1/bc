import json
from snapshottest import assert_match_snapshot

from wtosbc import wtos


def test_load_orders(snapshot):
    bc_number = "150"
    posts = load_test_posts()
    orders = wtos.get_orders(bc_number, posts)
    snapshot.assert_match(orders)


def load_test_posts():
    with open("tests/posts_150.json") as test_posts:
        return json.loads(test_posts.read())
