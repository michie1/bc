import requests
from lxml.cssselect import CSSSelector
from lxml.etree import fromstring
import lxml.html
from lxml import etree
import json
from wtosbc import config, wtos, spreadsheet, bc


def go() -> None:
    bc_number = load_bc_number()
    session = requests.Session()

    print("Session started")

    bc.login(session)

    posts = wtos.load_posts(bc_number)
    post_items_per_user = wtos.get_post_items_per_user(bc_number, posts)
    print("Orders loaded")

    if len(post_items_per_user) > 0:
        bc.clear_cart(session)
        print("Cart cleared")

        order_items_per_user = bc.add_cart(session, post_items_per_user)
        print("Orders added to cart")

        bc.add_pa(session, order_items_per_user)
        print("Price alerts added")

        # Remove PA/NON-PA items from cart
        bc.remove_cart(session, order_items_per_user)

        bc_spreadsheet = spreadsheet.load(bc_number)
        print("Spreadsheet loaded")

        spreadsheet.update(bc_spreadsheet, bc_number, order_items_per_user)

        print("Spreadsheet updated")

        print("Finished")
    else:
        print("No orders")


def load_bc_number() -> int:
    with open("wtosbc/state.json", "r") as fp:
        data = json.load(fp)
        return int(data["number"])


if __name__ == "__main__":
    go()
