import json
from snapshottest import assert_match_snapshot, Snapshot
from typing import cast, Any
from wtosbc.custom_types import Posts, OrderItemsPerUser
from wtosbc import spreadsheet

Snapshot = Any


def test_empty_cells(snapshot: Snapshot) -> None:
    cells = spreadsheet.get_cells({})
    snapshot.assert_match(cells)


def test_get_cells(snapshot: Snapshot) -> None:
    order_items_per_user = load_test_order_items_per_user()
    cells = spreadsheet.get_cells(order_items_per_user)
    snapshot.assert_match(cells)


def load_test_order_items_per_user() -> OrderItemsPerUser:
    with open("tests/order_items_per_user_194.json") as test_posts:
        return cast(OrderItemsPerUser, json.loads(test_posts.read()))
