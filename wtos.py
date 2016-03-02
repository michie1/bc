# -*- coding: utf-8 -*-
import requests
import lxml.html

def load_orders():

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




