import json
from snapshottest import assert_match_snapshot, Snapshot
from typing import cast, Any
import lxml.html
from wtosbc.custom_types import PostItem
from wtosbc import bc

Snapshot = Any


def test_get_product(snapshot: Snapshot) -> None:
    post_item: PostItem = {
        "url": "tests/product_page.html",
        "type": "silver-black/140 mm",
        "qty": 1,
        "pa": "",
    }
    html = load_test_product_page_html(post_item["url"])
    document = lxml.html.document_fromstring(html)
    product = bc.get_product(document, post_item)
    snapshot.assert_match(product)


def load_test_product_page_html(url: str) -> str:
    with open(url) as product_page:
        return product_page.read()
