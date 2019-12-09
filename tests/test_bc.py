import json
from snapshottest import assert_match_snapshot, Snapshot
from typing import cast, Any
from wtosbc.custom_types import Posts
from wtosbc import wtos

Snapshot = Any


def test_load_orders(snapshot: Snapshot) -> None:
    bc_number = 150
    posts = load_test_posts()
    post_items_per_user = wtos.get_post_items_per_user(bc_number, posts)
    snapshot.assert_match(post_items_per_user)


def load_test_posts() -> Posts:
    with open("tests/posts_150.json") as test_posts:
        return cast(Posts, json.loads(test_posts.read()))
