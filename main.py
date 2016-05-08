"""`main` is the top level module for your Flask application."""
#sys.path.insert(0, '/home/m/bc')
#import main_bc
import requests
from lxml.cssselect import CSSSelector
from lxml.etree import fromstring
import lxml.html
from lxml import etree
import json

from config import *
from wtos import load_orders, has_new_post
from ss import load_spreadsheet, add_to_spreadsheet
from bc import *

from google.appengine.api import memcache
from google.appengine.api import urlfetch
urlfetch.set_default_fetch_deadline(60)

# Import the Flask Framework
from flask import Flask
app = Flask(__name__)
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

def go():
    
    # Check if another instance is already busy
    if memcache.get("busy") == "1":
        print "Already busy"
    else:
        memcache.set("busy", "0")

        s = requests.Session()
        print 'Session started'

        # Login to BC
        login(s)

        bc_number = '110'

        # Load orders from WTOS
        orders = load_orders(bc_number)
        print 'Orders loaded'

        if len(orders) > 0:
            # First clear cart
            clear_cart(s)
            print 'Cart cleared'

            # Add to bc cart
            orders = add_cart(s, orders)
            print 'Orders added to cart'

            orders = add_pa(s, orders)
            print 'Price alerts added'

            # Load and reset spreadsheet
            wks = load_spreadsheet(bc_number)
            print 'Spreadsheet loaded'

            # Add to Google Spreadsheet
            add_to_spreadsheet(wks, orders)

            print 'Finished'
        else:
            print 'No orders'
        
        memcache.set("busy", "0")

@app.route('/check')
def check_route():
    if has_new_post():
        go()
        return "Updated"
    else:
        return "Nothing to do"

@app.route('/go')
def go_route():
    go()
    return "Updated"

@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, Nothing at this URL.', 404


@app.errorhandler(500)
def application_error(e):
    """Return a custom 500 error."""
    return 'Sorry, unexpected error: {}'.format(e), 500
