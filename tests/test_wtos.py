import json
from snapshottest import assert_match_snapshot, Snapshot
from typing import cast, Any
from wtosbc.custom_types import Posts
from wtosbc import wtos, config
import pytest

Snapshot = Any


def test_get_post_items_per_user(snapshot: Snapshot) -> None:
    bc_number = 150
    posts = load_test_posts()
    post_items_per_user = wtos.get_post_items_per_user(bc_number, posts)
    snapshot.assert_match(post_items_per_user)


def test_get_post_items_per_user_wrong_url() -> None:
    bc_number = 150
    assert wtos.get_post_items_per_user(
        bc_number,
        [{"display_name": "test_user", "post_content": "BC150\n1x http://wrong_url"}],
    ) == {"test_user": []}


def test_get_post_items_per_user_wtos_user() -> None:
    bc_number = 150
    post_items_per_user = wtos.get_post_items_per_user(
        bc_number,
        [
            {
                "display_name": config.bc_chef,
                "post_content": "BC150\nWTOS\n2x https://www.bike-components.de/en/Axa/RLC-100-Plug-In-Cable-Saddle-Bag-p54054/black-universal-o200001",
            }
        ],
    )
    expected = {
        "WTOS": [
            {
                "url": "https://www.bike-components.de/en/Axa/RLC-100-Plug-In-Cable-Saddle-Bag-p54054/black-universal-o200001",
                "type": "",
                "qty": 2,
                "pa": "",
            }
        ]
    }
    assert post_items_per_user == expected


def test_has_next_post() -> None:
    bc_chef = "Tim van Rugge"
    bc_number = 150
    posts = load_test_posts()
    assert wtos.has_next_post([], bc_number, bc_chef) == False
    assert wtos.has_next_post(posts, 0, bc_chef) == False
    assert wtos.has_next_post(posts, bc_number, "") == False
    assert wtos.has_next_post(posts, bc_number, bc_chef)


def test_split_type_pa() -> None:
    assert wtos.split_type_pa("") == ("", "")
    assert wtos.split_type_pa("type") == ("type", "")
    assert wtos.split_type_pa("[b]pa[/b]") == ("", "pa")
    assert wtos.split_type_pa("type [b]pa[/b]") == ("type", "pa")


def load_test_posts() -> Posts:
    with open("tests/posts_150.json") as test_posts:
        return cast(Posts, json.loads(test_posts.read()))
