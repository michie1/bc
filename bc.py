import lxml.html
import json
import time
from config import *

def login(s):
    r = s.get('https://www.bike-components.de/en/')
    r = s.get('https://www.bike-components.de/en/login/')

    doc = lxml.html.document_fromstring(r.text)
    # token = doc.cssselect('input[name="__token"]')[0].value
    # pdb.set_trace()
    token = doc.cssselect('input[name="module9200[login][_token]"]')[0].value
    print('Token retrieved: ', token)

    r = s.post(
    #'https://www.bike-components.de/login.php?action=process',
    'https://www.bike-components.de/en/login/',
        data = {
            #'email_address': email,
            'module9200[login][email]': email,
            'module9200[login][password]': password,
            'module9200[login][_token]': token,
            'module9200[login][submit]': ''
            #'password': password,
            # module9200[login][submit]
            #'__intention': 'login',
            #'__token': token
         })

    #pdb.set_trace()

    if r.text.find('Your shopping cart') == -1:
        print('Not logged in')
        exit()
    print('Logged in')

# Retrieve data about product in order to POST
def get_product_data(s, product):
    data = {}

    r = s.get(product['url'])
    doc = lxml.html.document_fromstring(r.text)

    #product['type'] = product.replace('&quot;', '"')

    try:

        #.strip('buy online')
        data['id'] = doc.cssselect('input[name="products_id"]')[0].get('value')
        data['name'] = doc.cssselect('title')[0].text.encode('utf-8').replace(' - bike-components', '').replace('buy online', '')
        #print data['id'], data['name']
        data['qty'] = str(product['qty'])
        data['pa'] = product['pa']




        #j = doc.cssselect('#jump-to-1')
        #print doc.cssselect('div.product-options')[0]
        #print lxml.html.tostring(doc.cssselect('li[itemprop="offers"]')[0])
        #print lxml.html.tostring(doc.cssselect('div.product-options li[itemprop="offers"]')[0])
        #ul li[itemprop="offers"]'):
        #print lxml.html.tostring(li)
        # pdb.set_trace()


        type_index = 0
        if product['type'] == '':
            # get default type
            li = doc.cssselect('li[itemprop="offers"]')[type_index]
            data['type'] = li.cssselect('span[itemprop="name"]')[0].text.strip()[0:-1]
        else:
            #print product['type']
            data['type'] = product['type']
            #print data['type'].encode('utf-8')

            li = doc.cssselect('li[itemprop="offers"]')[type_index]
            #print data['type'].encode('utf-8')
            #print li.cssselect('span[itemprop="name"]')[0].text.strip()[0:-1].encode('utf-8')
            while product['type'] != li.cssselect('span[itemprop="name"]')[0].text.strip()[0:-1]:
                type_index += 1
                li = doc.cssselect('li[itemprop="offers"]')[type_index]

            #print lxml.html.tostring(li)


        #print lxml.html.tostring(li)


        data['price'] = float(li.cssselect('meta[itemprop="price"]')[0].get('content'))
        data['sku'] = li.cssselect('meta[itemprop="sku"]')[0].get('content')

        options = doc.cssselect('div#module-product-detail-options')[0]

        if options.cssselect('option')[0].get('class') == 'placeholder':
            type_index += 1
        
        data['type_id'] = options.cssselect('option')[type_index].get('value')


        data['token'] = doc.cssselect('body')[0].get('data-csrf-token')
        #print data['type_id']

        #print lxml.html.tostring(option)

        #data['type'] = doc.cssselect('[data-selectedtext]')[0].get('data-selectedtext')
        #data['type_id'] = doc.cssselect('[data-selectedtext]')[0].get('value')

        # get sku based on type index
        # data['sku'] = doc.cssselect('meta[itemprop="sku"]')[type_index].get('content') 

        #data['price'] = float(doc.cssselect('[data-selectedtext]')[type_index].get('data-price')[0:-1].replace('.', '').replace(',', '.'))


        return data

    except IndexError as e:
        print('type does not exist?')
        print(data)
        print(e)
        return None
        #print product['url'] + ' ' + data['type'] + ' failed'
        # exit()

# Add a product to the cart
def add_product(s, product):
    data = get_product_data(s, product)

    if data != None:
        r = s.post('https://www.bike-components.de/callback/cart_product_add.php?ajaxCart=1', data = {
            'products_id': data['id'], 
            'id[1]': data['type_id'],
            'products_qty': data['qty'],
            'ajaxCart': '1',
            '_token': data['token']
            })

        if json.loads(r.text)['action'] != 'ok':
            print(r.text)
            exit()

    return data

# add price alert voucher
def add_pa(s, orders):
    #[{"type":"message","data":{"title":"The voucher code 9X86JPTZ has already been used in an order.","message":"Please contact our service team for questions or problems.","type":"type-error"}},{"type":"replace_components","data":[]}]

    """
    r = s.get('https://www.bike-components.de/en/checkout/login/')
    print r.text.encode('utf-8')
    doc = lxml.html.document_fromstring(r.text)
    profile_token = doc.cssselect('#complete_profile__token')[0].get('value')

    # billing information

    r = s.post('https://www.bike-components.de/en/checkout/login/',
            data = {
    'complete_profile[shipping][shipping_type]': 'billing_address',
    'complete_profile[_token]': profile_token,
    'submit': ''
                }
            )

    # payment information 

    doc = lxml.html.document_fromstring(r.text)
    payment_token = doc.cssselect('#payment__token')[0].get('value')

    r = s.post('https://www.bike-components.de/en/checkout/payment/',
            data = {
    'payment[type]': 'prepayment',
    'payment[_token]': payment_token,
    'payment[submit]': ''
                }
            )

    """

    r = s.get('https://www.bike-components.de/en/checkout/finalize/')
    #print r.text.encode('utf-8')
    #exit()
    doc = lxml.html.document_fromstring(r.text)
    voucher_token = doc.cssselect('#voucher__token')[0].get('value')
    print('voucher_token retrieved: ', voucher_token)

    # adding price alerts

    for user, products in orders.iteritems():
        for pid, product in enumerate(products):
            if product == None:
                continue

            if product['pa'] != '':
                #print product['pa']
                #product['pa'] = 'CAKEVPZS'

                #r = s.post('https://www.bike-components.de/en/checkout/api/',
                r = s.post('https://www.bike-components.de/en/checkout/finalize/',
                        data = {
                            #'actions[0][type]': 'add_voucher',
                            #'actions[0][parameters][voucher_code]': product['pa'],
                            #'actions[1][type]': 'render_all',
                            'voucher[voucher_code]': product['pa'],
                            'voucher[_token]': voucher_token,
                            #'_token': 'e868698615adaad6042d3ec7e480c6933d1e260e'
                            }
                        )
#_token=e868698615adaad6042d3ec7e480c6933d1e260e
#actions[0][parameters][voucher_code]=khkjh
#actions[0][type]=add_voucher
#actions[1][type]=render_all

                doc = lxml.html.document_fromstring(r.text)
                #voucher_token = doc.cssselect('#voucher__token')[0].get('value')
                #print 'voucher_token: ', voucher_token
                #print r.text.encode('utf-8')
                
                try:
                    pa_price = doc.cssselect('div.row [data-voucher-code="' + product['pa'] + '"]')[0].getparent().getparent().getparent().cssselect('.price-single .value.discounted')[0].text.strip().replace(',', '.')[0:-1]
                    product['price'] = pa_price
                except IndexError as e:
                    print('Something wrong with price alert: ' + product['pa'])
                    print(e)
            time.sleep(1)

                #orders[user][pid]['pa_price'] = pa_price

                #print r.json()

                #r = s.get('https://www.bike-components.de/shopping_cart.php?language=en')
                #r = s.post('https://www.bike-components.de/en/checkout/login/')
                #r = s.get('https://www.bike-components.de/en/checkout/finalize/')
                #r = s.get('https://www.bike-components.de/shopping_cart.php?language=en')

                #r = s.post('https://www.bike-components.de/en/checkout/api/',
                        #data = {'actions': [{'type': 'add_voucher', 'parameters':{'voucher_code':'hoi'}}, {'type': 'render_all'}], '_token': })
                #token = r.text.split('csrf_token')
                #print 'token' in r.text
                #print 'finalize' in r.text
                #print r.text
                #print token
                #print r.text.encode('utf-8')

    return orders

# Add all orders to the cart
# and add extra data 
def add_cart(s, orders):
    for user, products in orders.iteritems():
        #print user, order
        for pi, product in enumerate(products):
            #if product['url'] != 'https://www.bike-components.de/en/Procraft/Allround-II-MTB-Cage-Pedals-p13419/':
                #continue

            data = add_product(s, product)
            if data != None:
                orders[user][pi]['price'] = data['price']
                orders[user][pi]['original_price'] = data['price']
                orders[user][pi]['price'] = data['price']
                orders[user][pi]['pa'] = data['pa']
                orders[user][pi]['name'] = data['name']
                orders[user][pi]['type'] = data['type']
                orders[user][pi]['sku'] = data['sku']
            else:
                orders[user][pi] = None
                #print pi
                #print orders[user]
                #exit()
                #orders[user].pop(pi)

        print('Order ' + user + ' added to cart')

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

