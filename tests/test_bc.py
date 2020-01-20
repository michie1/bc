import json
from snapshottest import assert_match_snapshot, Snapshot
from typing import cast, Any
import lxml.html
from wtosbc.custom_types import PostItem, OrderItemsPerUser, Payloads
from wtosbc import bc
import pytest

Snapshot = Any


def test_get_product(snapshot: Snapshot) -> None:
    post_item: PostItem = {
        "url": "tests/product_page.html",
        "type": "silver-black/140 \" ″'mm",
        "qty": 1,
        "pa": "",
    }
    html = load_test_product_page_html(post_item["url"])
    document = lxml.html.document_fromstring(html)
    product = bc.get_product(document, post_item)
    snapshot.assert_match(product)


def test_combine_order_items() -> None:
    order_items_per_user = load_test_order_items_per_user()
    order_items = bc.get_payloads(order_items_per_user)
    expected_order_items: Payloads = [
        {
            "id": "46718",
            "quantity": 4,
            "token": "44b3daca3f1958cd7dc7c1eb511beef68764769f",
            "type_id": "200241",
        }
    ]

    assert order_items == expected_order_items


def load_test_product_page_html(url: str) -> str:
    with open(url) as product_page:
        return product_page.read()


def load_test_order_items_per_user() -> OrderItemsPerUser:
    with open(
        "tests/order_items_per_user_double_order_items.json"
    ) as order_items_per_user:
        return cast(OrderItemsPerUser, json.loads(order_items_per_user.read()))
