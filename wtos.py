# -*- coding: utf-8 -*-
import requests
import lxml.html
#import untangle
import xmltodict
import urllib2

from google.appengine.api import memcache

def load_orders(bc_number):
    #obj = untangle.parse('http://www.wtos.nl/prikbord/index.php?action=.xml;limit=100;board=5.0')
    #print obj.smf_xml_feed.recent_post[0].starter.name.cdata

    orders = {}

    file = urllib2.urlopen('http://www.wtos.nl/prikbord/index.php?action=.xml;limit=30;board=5.0')
    data = file.read()
    file.close()
    print 'Posts loaded'

    xml = xmltodict.parse(data)

    for post_obj in xml.items()[0][1:][0].items()[3][1]:
        post = post_obj.values()
        topic_id = post[6].values()[1]
        if topic_id == '6335':
            #doc = lxml.html.document_fromstring(html)
            if True or post[1] == '78403':
                #if post[3][2:5] == str(bc_number):
                if post[3][2:6] == str(bc_number): # want BC1234
                    poster_name = post[5].values()[0]
                    orders[poster_name] = []
                    lines = post[3].split('<br />')[1:]
                    for line in lines:
                        if line != '':
                            if line == '---':
                                break
                            else:
                                try:
                                    product_qty, product = line.split('x ', 1)
                                except ValueError as e:
                                    print 'Error'
                                    print e
                                    continue

                                if int(product_qty) > 0:
                                    product_url = product[9:].split('"')[0]
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

                                    orders[poster_name].append({
                                        'url': product_url,
                                        'type': product_type,
                                        'qty': int(product_qty),
                                        'pa': product_pa
                                    })
                    print 'Order ' + poster_name + ' loaded'
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
        print 'Topic loaded'
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
    file = urllib2.urlopen('http://www.wtos.nl/prikbord/index.php?action=.xml;limit=10;board=5.0')
    data = file.read()
    file.close()

    latest_post_id = -1 # None found in last 10 posts
    xml = xmltodict.parse(data)
    for post_obj in xml.items()[0][1:][0].items()[3][1]:
        post = post_obj.values()
        topic_id = post[6].values()[1]
        if topic_id == '6317':
            latest_post_id = post[1]
            break

    if latest_post_id == -1:
        return False

    
    if latest_post_id != memcache.get("latest_post_id"):
        memcache.set("latest_post_id", latest_post_id)
        return True

    return False
