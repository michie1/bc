import lxml.html
import json
import time
import config

def login(s):
    r = s.get('https://www.bike-components.de/en/')
    r = s.get('https://www.bike-components.de/en/light-login/')

    doc = lxml.html.document_fromstring(r.text)
    token = doc.cssselect('input[name="login[_token]"]')[0].value
    print('Token retrieved: ', token)

    r = s.post(
    'https://www.bike-components.de/en/light-login/',
        data = {
            'login[email]': config.email,
            'login[password]': config.password,
            'login[_token]': token,
            'login[redirect]': ''
         })

    if r.text.find('Mein Konto') == -1:
        print('Not logged in')
        exit()
    print('Logged in')

# Retrieve data about product in order to POST
def get_product_data(s, product):
    data = {}

    r = s.get(product['url'])
    doc = lxml.html.document_fromstring(r.text)

    try:
        data['id'] = doc.cssselect('input[name="products_id"]')[0].get('value')
        data['name'] = doc.cssselect('title')[0].text.replace(' - bike-components', '').replace('buy online', '').replace('online kaufen', '').encode('utf-8')
        data['qty'] = str(product['qty'])
        data['pa'] = product['pa']

        type_index = 0
        options = doc.cssselect('option[data-price]')

        if product['type'] == '':
            option = options[type_index]
            option_type_name = get_option_type_name(option)
        else:
            option = options[type_index]
            option_type_name = get_option_type_name(option)

            # Originally we had to remove the last character, but BC changed something
            # so now we do two comparisons, with and without the last character.
            while product['type'] != option_type_name[0:-1] and product['type'] != option_type_name:
                    type_index += 1
                    option = options[type_index]
                    option_type_name = get_option_type_name(option)


        data['type'] = product['type']
        data['price'] = float(option.get('data-price')[0:-1].replace(',', '.')) # remove last euro char
        data['type_id'] = option.get('value')

        data['token'] = doc.cssselect('body')[0].get('data-csrf-token')

        return data

    except IndexError as e:
        print('Item/type does not exist?')
        print(e)
        print(data)
        exit()
        return None

def get_option_type_name(option):
    return option.text_content().split('|')[0].strip()

# Add a product to the cart
def add_product(s, product):
    data = get_product_data(s, product)

    if data != None:
        r = s.post('https://www.bike-components.de/callback/cart_product_add.php?ajaxCart=1', data = {
            'products_id': data['id'],
            'id[1]': data['type_id'],
            'quantity': data['qty'],
            'ajaxCart': '1',
            '_token': data['token']
            })

        if json.loads(r.text)['action'] != 'ok':
            exit()

    return data

# add price alert voucher
def add_pa(s, orders):
    r = s.get('https://www.bike-components.de/en/checkout/finalize/')
    doc = lxml.html.document_fromstring(r.text)

    voucher_token = doc.cssselect('#voucher__token')[0].get('value')
    print('voucher_token retrieved: ', voucher_token)

    # adding price alerts
    for user, products in orders.items():
        for pid, product in enumerate(products):
            if product == None:
                continue

            if product['pa'] != '':

                r = s.post('https://www.bike-components.de/en/checkout/finalize/',
                        data = {
                            'voucher[voucher_code]': product['pa'],
                            'voucher[_token]': voucher_token,
                            }
                        )
                doc = lxml.html.document_fromstring(r.text)

                try:
                    pa_price = doc.cssselect('div.row [data-voucher-code="' + product['pa'] + '"]')[0].getparent().getparent().getparent().cssselect('.price-single .value.discounted')[0].text.strip().replace(',', '.')[0:-1]
                    product['price'] = pa_price
                except IndexError as e:
                    print('Something wrong with price alert: ' + product['pa'], 'maybe already used')
            time.sleep(1)

    return orders

def remove_product(s, product_id, type_id):
    r = s.get('https://www.bike-components.de/shopping_cart.php')
    doc = lxml.html.document_fromstring(r.text)
    token = doc.cssselect('body')[0].get('data-csrf-token')

    r = s.post(
        'https://www.bike-components.de/callback/cart_update.php',
        data = {
            'cart_delete[]': product_id + '-' + type_id,
            'products_id[]products_id': product_id + '-' + type_id,
            '_token': token
        })

def read_state():
    with open('wtosbc/state.json', 'r') as file_read:
        data = json.load(file_read)
        return data

# Add all orders to the cart
# and add extra data
def add_cart(s, orders):
    for user, products in orders.items():
        for pi, product in enumerate(products):
            data = add_product(s, product)
            if data != None:
                orders[user][pi]['id'] = data['id']
                orders[user][pi]['type_id'] = data['type_id']
                orders[user][pi]['price'] = data['price']
                orders[user][pi]['original_price'] = data['price']
                orders[user][pi]['price'] = data['price']
                orders[user][pi]['pa'] = data['pa']
                orders[user][pi]['name'] = data['name']
                orders[user][pi]['type'] = data['type']
            else:
                orders[user][pi] = None

    return orders

def remove_cart(s, orders):
    state = read_state()
    for user, products in orders.items():
        for pi, product in enumerate(products):
            # Remove price alert product from basket if state is not pa
            if (not state['pa'] and product['pa'] != '') or (state['pa'] and product['pa'] == ''):
                print('Remove product ', product['id'], product['type_id'], state['pa'])
                remove_product(s, product['id'], product['type_id'])


    print('Removed items from cart')

    return orders

def clear_cart(s):
    # Get cart
    r = s.get('https://www.bike-components.de/shopping_cart.php')
    doc = lxml.html.document_fromstring(r.text)
    token = doc.cssselect('body')[0].get('data-csrf-token')

    for product in doc.cssselect('input[name="products_id[]"]'):
        r = s.post('https://www.bike-components.de/callback/cart_update.php',
            data = {
                'cart_delete[]': product.get('value'),
                'products_id[]products_id': product.get('value'),
                '_token': token
            })
