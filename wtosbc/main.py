import requests
from lxml.cssselect import CSSSelector
from lxml.etree import fromstring
import lxml.html
from lxml import etree
import json

from wtosbc import config, wtos, spreadsheet, bc

def load_bc_number() -> int:
    with open('wtosbc/state.json', 'r') as fp:
        data = json.load(fp)
        return int(data['number'])

def go() -> None:
    s = requests.Session()
    print('Session started')

    # Login to BC
    bc.login(s)

    # bc_number = '123'
    bc_number = load_bc_number()

    # Load orders from WTOS
    posts = wtos.load_posts(bc_number)
    orders = wtos.get_orders(bc_number, posts)
    print('Orders loaded')

    if len(orders) > 0:
        # First clear cart
        bc.clear_cart(s)
        print('Cart cleared')

        # Add to bc cart
        orders_extended = bc.add_cart(s, orders)
        print('Orders added to cart')

        bc.add_pa(s, orders_extended)
        print('Price alerts added')

        # Remove PA/NON-PA items from cart
        bc.remove_cart(s, orders_extended)

        # Load and reset spreadsheet
        wks = spreadsheet.load_spreadsheet(bc_number)
        print('Spreadsheet loaded')

        # Add to Google Spreadsheet
        spreadsheet.add_to_spreadsheet(wks, orders_extended)

        print('Finished')
    else:
        print('No orders')

if __name__ == "__main__":
    go()
