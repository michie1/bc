import lxml.html
import json
import time
from typing import Any, List, Dict, Optional, cast
from mypy_extensions import TypedDict
from wtosbc import config

Session = Any

def login(s: Session) -> None:
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

class ProductData(TypedDict):
    id: str
    name: str
    qty: str
    pa: str
    type: str
    price: float
    type_id: str
    token: str

class Product(TypedDict):
    url: str
    type: str
    qty: int
    pa: str

# Retrieve data about product in order to POST
def get_product_data(s: Session, product: Product) -> Optional[ProductData]:
    data: ProductData = {
        'id': '',
        'name': '',
        'qty': '',
        'pa': '',
        'type': '',
        'price': 0,
        'type_id': '',
        'token': ''
    }

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
            option_type_name = get_option_type_name(option.text_content())
        else:
            option = options[type_index]
            option_type_name = get_option_type_name(option.text_content())

            # Originally we had to remove the last character, but BC changed something
            # so now we do two comparisons, with and without the last character.
            while product['type'] != option_type_name[0:-1] and product['type'] != option_type_name:
                    type_index += 1
                    option = options[type_index]
                    option_type_name = get_option_type_name(option.text_content())


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

def get_option_type_name(text_content: str) -> str:
    return text_content.split('|')[0].strip()

# Add a product to the cart
def add_product(s: Session, product: Product) -> ProductData:
    data = get_product_data(s, product)

    if data is None:
        exit()

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

class OrderItem(TypedDict):
    url: str
    type: str
    qty: int
    pa: str
    id: str
    type_id: str
    price: float
    original_price: float
    name: str

Orders = Dict[str, List[Optional[OrderItem]]]

# add price alert voucher
def add_pa(s: Session, orders: Orders) -> None:
    r = s.get('https://www.bike-components.de/en/checkout/finalize/')
    doc = lxml.html.document_fromstring(r.text)

    voucher_token = doc.cssselect('#voucher__token')[0].get('value')
    print('voucher_token retrieved: ', voucher_token)

    # adding price alerts
    for user, products in orders.items():
        for pid, product in enumerate(products):
            if product is None:
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

def remove_product(s: Session, product_id: str, type_id: str) -> None:
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

class State(TypedDict):
    number: int
    pa: bool
    state: bool

# Add all orders to the cart
# and add extra data
def add_cart(s: Session, orders: Any) -> Any:
    for user, products in orders.items():
        for pi, product in enumerate(products):
            if product is not None:
                data = add_product(s, product)
                if data is not None:
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

def read_state() -> State:
    with open('wtosbc/state.json', 'r') as file_read:
        data = json.load(file_read)
        return cast(State, data)

def remove_cart(s: Session, orders: Orders) -> None:
    state = read_state()
    for user, products in orders.items():
        for pi, product in enumerate(products):
            if product is not None:
                # Remove price alert product from basket if state is not pa
                if (not state['pa'] and product['pa'] != '') or (state['pa'] and product['pa'] == ''):
                    print('Remove product ', product['id'], product['type_id'], state['pa'])
                    remove_product(s, product['id'], product['type_id'])

    print('Removed items from cart')

def clear_cart(s: Session) -> None:
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
