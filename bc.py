import lxml.html
import json
from config import *

def login(s):
    r = s.get('https://www.bike-components.de/en/')
    r = s.get('https://www.bike-components.de/login.php')

    doc = lxml.html.document_fromstring(r.text)
    token = doc.cssselect('input[name="__token"]')[0].value
    print 'Token retrieved: ', token

    r = s.post('https://www.bike-components.de/login.php?action=process',
        data = {
            'email_address': email,
            'password': password,
            '__intention': 'login',
            '__token': token
         })

    if r.text.find('Your shopping cart contains') == -1:
        print 'Not logged in'
        exit()
    print 'Logged in'

# Retrieve data about product in order to POST
def get_product_data(s, product):

    data = {}
    r = s.get(product['url'])
    doc = lxml.html.document_fromstring(r.text)

    try:
        data['id'] = doc.cssselect('[name="products_id"]')[0].get('value')
        data['name'] = doc.cssselect('title')[0].text.strip(' - bike-components')
        data['qty'] = product['qty']

        # get type id
        if product['type'] != '':
            data['type'] = product['type']
            data['type_id'] = doc.cssselect('[data-selectedtext="' + data['type'] + '"]')[0].get('value')

        else:
            # get default type
            data['type'] = doc.cssselect('[data-selectedtext]')[0].get('data-selectedtext')
            data['type_id'] = doc.cssselect('[data-selectedtext]')[0].get('value')


        data['price'] = float(doc.cssselect('[data-selectedtext="' + data['type'] + '"]')[0].text_content().split(' | ')[1][0:-1].replace(',', '.'))

        return data

    except IndexError as e:
        print product['url'] + ' ' + data['type'] + ' failed'
        exit()

# Add a product to the cart
def add_product(s, product):
    data = get_product_data(s, product)

    r = s.post('https://www.bike-components.de/callback/cart_product_add.php?ajaxCart=1', data = {
        'products_id': data['id'], 
        'id[1]': data['type_id'],
        'products_qty': data['qty']
        })

    if json.loads(r.text)['action'] != 'ok':
        print product_id + ' ' + product_type_id + ' failed'
        exit()

    return data

# Add all orders to the cart
# and add extra data 
def add_cart(s, orders):
    for user, products in orders.iteritems():
        #print user, order
        for pi, product in enumerate(products):
            data = add_product(s, product)
            orders[user][pi]['price'] = data['price']
            orders[user][pi]['name'] = data['name']
            orders[user][pi]['type'] = data['type']

    return orders
