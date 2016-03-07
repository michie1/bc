import requests
from lxml.cssselect import CSSSelector
from lxml.etree import fromstring
import lxml.html
from lxml import etree
import json

from config import *
from wtos import load_orders
from google import *
from bc import *

POST_BC = False
READ_WTOS = True
POST_SPREADSHEET = False

s = requests.Session()
print 'Session started'


#topic_url = 'http://www.wtos.nl/prikbord/index.php?topic=6126.msg78335;topicseen#new'

#t = requests.get(topic_url)
#doc = lxml.html.document_fromstring(t.text)
#print 'Topic loaded'
#last_post = doc.cssselect('[class=post]')[-2][0]
#print 'Last post loaded'

#order_number = last_post[0].text_content()
#print 'Order number loaded'
#print last_post.text_content()
#product_url = last_post[3].get('href')
#print product_url

#post_html = 'BC105<br />2x <a href="https://www.bike-components.de/en/Shimano/Ultegra-FC-CX70-105-Innenlager-SM-BBR60-Hollowtech-II-p35878/" class="bbc_link" target="_blank">https://www.bike-components.de/en/Shimano/Ultegra-FC-CX70-105-Innenlager-SM-BBR60-Hollowtech-II-p35878/</a> schwarz/BSA<br />1x</strong> <a href="https://www.bike-components.de/en/BBB/RaceRibbon-BHT-01-Korklenkerband-p5064/" class="bbc_link" target="_blank">https://www.bike-components.de/en/BBB/RaceRibbon-BHT-01-Korklenkerband-p5064/</a> schwarz/BHT-01'

#order_number = post_html[2:5]
#print 'BC' + order_number




#product_url = 'https://www.bike-components.de/en/Shimano/Ultegra-Kassette-CS-6700-10-fach-p22072/'
#product_type = 'silber/11-29'

#product_url = 'https://www.bike-components.de/en/Shimano/Ultegra-XT-E-Bike-Kette-CN-HG701-11-11-fach-Modell-2016-p44481/'
#product_type = ''
#product_qty = '1'

# moet naar wtos.py
if False:
    price_sum = 0.0
    for p in post_html.split('<br />')[1:]:
#for p in post_html.split('<br />')[1:2]:
        product_qty = int(p.split('x')[0])
        product_type = p.split('</a> ')[-1]
        product_url = p.split('href=\"')[1].split('"')[0]

        #print product_qty, product_url, product_type
        r = s.get(product_url)
        doc = lxml.html.document_fromstring(r.text)

        try:
            product_id = doc.cssselect('[name="products_id"]')[0].get('value')
            
            if product_type != '':
                product_type_id = doc.cssselect('[data-selectedtext="' + product_type + '"]')[0].get('value')

            else:
                product_type = doc.cssselect('[data-selectedtext]')[0].get('data-selectedtext')
                product_type_id = doc.cssselect('[data-selectedtext]')[0].get('value')

            product_name = doc.cssselect('title')[0].text.strip(' - bike-components')
            product_price = float(doc.cssselect('[data-selectedtext="' + product_type + '"]')[0].text_content().split(' | ')[1][0:-1].replace(',', '.'))

        except IndexError as e:
            print product_url + ' ' + product_type + ' failed'
            exit()

        if POST_BC:
            r = s.post('https://www.bike-components.de/callback/cart_product_add.php?ajaxCart=1', data = {
                'products_id': product_id, 
                'id[1]': product_type_id,
                'products_qty': product_qty
                })

        if json.loads(r.text)['action'] != 'ok':
            print product_id + ' ' + product_type_id + ' failed'
            exit()

    price_sum += product_qty * product_price
    print product_name + ' ' + product_type + ' ' + str(product_qty) + ' ' + str(product_price)

    print 'Products placed in shopping cart'
    print 'Price sum: ' + str(price_sum)

# Login to BC
#login(s)

bc_number = '106'

# Load orders from WTOS
orders = load_orders(bc_number)
print 'Orders loaded'

# Add to bc cart
orders = add_cart(s, orders)
print 'Orders added to cart'

# Load and reset spreadsheet
wks = load_spreadsheet()
print 'Spreadsheet loaded'

# Add to Google Spreadsheet
add_spreadsheet(orders)

print 'Finished'
