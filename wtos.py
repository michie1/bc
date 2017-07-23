# -*- coding: utf-8 -*-
import requests
import lxml.html
#import untangle
import xmltodict
from urllib.request import urlopen
import json
from ss2 import create_sheet
from config import *

def increment_bc_number(number):
    print('increment bc number')
    with open(directory + 'state.json', 'r') as file_read:
        data = json.load(file_read)
        with open(directory + 'state.json', 'w') as file_write:
            data['number'] = number
            json.dump(data, file_write)

def create_next_sheet(number):
    print('create next sheet')
    create_sheet(number)


def set_state_pa():
    print('set PA state')
    with open(directory + 'state.json', 'r') as file_read:
        data = json.load(file_read)
        with open(directory + 'state.json', 'w') as file_write:
            data['state'] = True
            json.dump(data, file_write)

def reset_state_pa():
    print('reset PA state')
    with open(directory + 'state.json', 'r') as file_read:
        data = json.load(file_read)
        with open(directory + 'state.json', 'w') as file_write:
            data['state'] = False
            json.dump(data, file_write)

def load_orders(bc_number):
    #obj = untangle.parse('http://retro.wtos.nl/prikbord/index.php?action=.xml;limit=100;board=5.0')
    #print obj.smf_xml_feed.recent_post[0].starter.name.cdata

    bc_chef = 'Tim.'

    orders = {}

    # maybe need to increase 80 when there are more posts between two orders.
    file = urlopen('http://www.wtos.nl/prikbord/index.php?action=.xml;limit=80;board=5.0')
    data = file.read()
    file.close()
    print('Posts loaded')

    xml = xmltodict.parse(data)

    recent_posts = xml["smf:xml-feed"]['recent-post']

    #for post_obj in xml.items()[0][1:][0].items()[3][1]:
    for post_obj in recent_posts:
        #import pdb; pdb.set_trace()
        #post = post_obj.values()
        #topic_id = post[6].values()[1]
        topic_id = post_obj['topic']['id']
        if topic_id == '6335':
            #doc = lxml.html.document_fromstring(html)
            if True:
                #if post[3][2:5] == str(bc_number):
                if post_obj['body'][2:11] == str(int(bc_number) + 1) + ' start': # next start
                    poster_name = post_obj['poster']['name']
                    if poster_name == bc_chef:
                        increment_bc_number(int(bc_number) + 1)
                        reset_state_pa()
                        create_next_sheet(int(bc_number) + 1)
                        break
                elif post_obj['body'][2:11] == str(int(bc_number) + 1) + ' PA': # next start
                    poster_name = post_obj['poster']['name']
                    if poster_name == bc_chef:
                        set_state_pa()
                        break
                elif post_obj['body'][2:11] == str(bc_number) + ' start': # current start
                    break # ignore
                elif post_obj['body'][2:5] == str(bc_number): # BC123 
                    poster_name = post_obj['poster']['name']
                    if poster_name not in orders:
                        orders[poster_name] = []
                    lines = post_obj['body'].split('<br />')[1:]
                    for line in lines:
                        if line != '':
                            if line == '---' or line == '--':
                                break
                            elif line[0] == '-' and line[-1] == '-':
                                continue
                            elif line[0:2] == '<a':
                                line = '1x ' + line
                            
                            if line[0:5] == '<del>':
                                continue
                            elif line == 'WTOS':
                                if poster_name == bc_chef:
                                    poster_name = 'WTOS'
                                    orders[poster_name] = []
                                else:
                                    break
                            else:
                                try:
                                    product_qty, product = line.split('x ', 1)
                                    product_qty = int(product_qty.strip())
                                except ValueError as e:
                                    print('ValueError')
                                    print(e)
                                    print(line)
                                    continue

                                if product_qty > 0:
                                    product_url = product[9:].split('"')[0]

                                    if 'bike-components.de' in product_url:
                                        #product_type = product.split('</a>')[1].strip()
                                            
                                        # Divide type  and pa
                                        type_pa = product.split('</a>')[1].strip()
                                        strong = type_pa.split('<strong>')

                                        # type and PA exists
                                        if len(strong) == 2:
                                            product_type = strong[0].strip()
                                            product_pa = strong[1].replace('</strong>', '').strip()
                                        else:
                                            # type or PA exist
                                            if type_pa[0:8] == "<strong>":
                                                # PA
                                                product_pa = type_pa[8:-9]
                                                product_type = ''
                                            else:
                                                # type
                                                product_type = type_pa 
                                                product_pa = ''

                                        # fix for " in type
                                        product_type = product_type.replace('&quot;', '"').replace('&nbsp;', '').strip()

                                        orders[poster_name].append({
                                            'url': product_url,
                                            'type': product_type,
                                            'qty': product_qty,
                                            'pa': product_pa
                                        })
                                    else:
                                        print('Wrong url: ', product_url)
                    #print(poster_name.encode('latin1'))
                    #print('Order ' + poster_name.encode('latin1') + ' loaded')
                    #break
                        #print post[3]

            #html = post.items()[3][1]
            #print html
            #print post.items()
        #[0].items()[0][1]

    #topic_id = recent_post.items()[6][1].items()[1][1]
    #print topic_id

    #print orders

    return orders

def load_orders_test(number):

    topic_url = 'http://www.wtos.nl/prikbord/index.php?topic=6126.msg78335;topicseen#new'

    if False:
        t = requests.get(topic_url)
        doc = lxml.html.document_fromstring(t.text)
        print('Topic loaded')
        last_post = doc.cssselect('[class=post]')[-2][0]

    #print last_post.text_content()[0:5]
    #print last_post.text_content()
    #print 'Last post loaded'

    orders = {
        'Michiel91':
            [{
                'url': 'https://www.bike-components.de/en/FSA/Auspresswerkzeug-EE0019-fuer-BB30-p21648/',
                'type': 'silber/universal',
                'qty': 1,
                'PA': ''
            },
            { 
                'url': 'https://www.bike-components.de/en/FSA/Einpresswerkzeug-EE041-fuer-BB30-p21646/',
                'type': 'silber/universal',
                'qty': 1,
                'PA': ''
            }]

        }
    return orders

def has_new_post():
    file = urllib.urlopen('http://www.wtos.nl/prikbord/index.php?action=.xml;limit=10;board=5.0')
    data = file.read()
    file.close()

    latest_post_id = -1 # None found in last 10 posts
    xml = xmltodict.parse(data)
    for post_obj in xml.items()[0][1:][0].items()[3][1]:
        post = post_obj.values()
        topic_id = post[6].values()[1]
        if topic_id == '6335':
            latest_post_id = post[1]
            break

    if latest_post_id == -1:
        return False

    return False
