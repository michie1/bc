import requests
from lxml.cssselect import CSSSelector
from lxml.etree import fromstring
import lxml.html
from lxml import etree
import json

from config import *
from wtos import load_orders, has_new_post
from ss2 import load_spreadsheet, add_to_spreadsheet
from bc import *



def read_bc_number():
    with open(directory + 'state.json', 'r') as fp:
        data = json.load(fp)
        return data['number']


def go():
    s = requests.Session()
    print('Session started')

    # Login to BC
    login(s)

    # bc_number = '123'
    bc_number = str(read_bc_number())

    # Load orders from WTOS
    orders = load_orders(bc_number)
    print('Orders loaded')

    if len(orders) > 0:
        # First clear cart
        clear_cart(s)
        print('Cart cleared')

        # Add to bc cart
        orders = add_cart(s, orders)
        print('Orders added to cart')

        orders = add_pa(s, orders)
        print('Price alerts added')

        # Remove PA/NON-PA items from cart
        orders = remove_cart(s, orders)

        # Load and reset spreadsheet
        wks = load_spreadsheet(bc_number)
        print('Spreadsheet loaded')

        # Add to Google Spreadsheet
        add_to_spreadsheet(wks, orders)

        print('Finished')
    else:
        print('No orders')
        

if __name__ == "__main__":
    go()
