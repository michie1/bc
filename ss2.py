import json
import gspread
import math
from oauth2client.service_account import ServiceAccountCredentials
import time
import pdb
from config import directory

def create_sheet(bc_number):
    print('Load Google credentials')
    json_key = json.load(open(directory + 'credentials.json'))
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(directory + 'credentials.json', scope)

    gc = gspread.authorize(credentials)
    sh = gc.open_by_key('1PgxD5wx6qrWtIfnJ89fdczpS6yKK5BOZZHcRQeZCnD4')

    sh.worksheets() # problem if this is removed
    sh.add_worksheet(title='BC' + str(bc_number), rows='1', cols='1')

def load_spreadsheet(bc_number):
    print('Load Google credentials')
    json_key = json.load(open(directory + 'credentials.json'))
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(directory + 'credentials.json', scope)

    gc = gspread.authorize(credentials)
    sh = gc.open_by_key('1PgxD5wx6qrWtIfnJ89fdczpS6yKK5BOZZHcRQeZCnD4')

    sh.worksheets() # problem if this is removed
    sh.add_worksheet(title='0', rows='1', cols='1')


    try:
        # delete worksheet
        sh.del_worksheet(sh.worksheet("BC" + str(bc_number)))
    except gspread.exceptions.WorksheetNotFound as err:
        print(err)
    
    # make worksheet
    wks = sh.add_worksheet(title='BC' + str(bc_number), rows='200', cols='10')
    #wks = sh.worksheet('105_cart')

    sh.del_worksheet(sh.worksheet('0'))
    
    return wks

def add_to_spreadsheet(wks, orders):

    #orders = sorted(orders)

    cell_list = wks.range("A1:J%s" % 200)
    #print cell_list
    #pdb.set_trace()

    row_number = 0

    #header[0].value = 'besteller'
    #header[1].value = 'artikel'
    #header[2].value = 'type'
    #header[3].value = 'sku'
    cell_list[4].value = 'Price alert'
    cell_list[5].value = 'Originele prijs'
    cell_list[6].value = 'Prijs per stuk'
    cell_list[7].value = 'Aantal'
    cell_list[8].value = 'Totaal'
    cell_list[9].value = '5%'
    #wks.update_cells(header)
    row_number += 1

    summary = []
    
    #for user, products in orders.iteritems():
    for user, products in sorted(orders.items()):
        if len(products) > 0:
            cell_list[row_number*10].value = user # no decode ni python 3.5
            row_number += 1
            first_row = row_number

            for product in products:
                if product == None:
                    continue

                try:
                    cell_list[row_number*10+0].value, cell_list[row_number*10+1].value = product['name'].decode('utf-8').split(' ', 1) # no decode in python3.5
                    # cell_list[row_number*10+0].value, cell_list[row_number*10+1].value = product['name'].split(' ', 1)
                except IndexError as e:
                    print(e)
                    print(user, product)
                    print(product['type'])
                    print(row_number)
                    continue
                except KeyError as e:
                    print(e)
                    print(user, product)
                    continue

                cell_list[row_number*10+2].value = product['type']
                cell_list[row_number*10+3].value = "=(\"" + product['sku'] + "\")"
                cell_list[row_number*10+4].value = product['pa']
                
                # todo ceiling
                cell_list[row_number*10+5].value = product['original_price']
                cell_list[row_number*10+6].value = product['price']

                cell_list[row_number*10+7].value = product['qty']
                cell_list[row_number*10+8].value = "=G" + str(row_number+1) + "*H" + str(row_number+1)
                cell_list[row_number*10+9].value = "=CEILING(I" + str(row_number+1) + "*0.95, 0.01)"
                row_number += 1

            last_row = row_number - 1

            cell_list[row_number*10+8].value = '=SUM(I' + str(first_row+1) + ':I' + str(last_row+1) + ')'
            cell_list[row_number*10+9].value = '=SUM(J' + str(first_row+1) + ':J' + str(last_row+1) + ')'

            summary.append((user, '=SUM(J' + str(first_row+1) + ':J' + str(last_row+1) + ')'))

            #try:
                #cell_list[row_number+8].value = '=SUM(I' + str(first_row) + ':I' + str(last_row) + ')'
                #cell_list[row_number+9].value = '=SUM(J' + str(first_row) + ':J' + str(last_row) + ')'
            #except gspread.exceptions.ConnectionError as err:
                #print err
                #memcache.set("busy", "0")

            row_number += 2
            # print('Order ' + user + ' prepared for spreadsheet')
            #time.sleep(1)

    start_row_total_sum = row_number + 1
    for user_sum in summary:
        cell_list[row_number*10].value = user_sum[0]
        cell_list[row_number*10+1].value = user_sum[1]
        row_number += 1
    end_row_total_sum = row_number

    row_number += 1

    cell_list[row_number*10].value = "Totaal"
    cell_list[row_number*10+1].value = "=SUM(B" + str(start_row_total_sum) + ":B" + str(end_row_total_sum) + ")"
    row_number += 1

    cell_list[row_number*10].value = "zonder 5%"
    cell_list[row_number*10+1].value = "=B" + str((row_number)) + "/0.95"
    row_number += 1

    cell_list[row_number*10].value = "Met porto"
    cell_list[row_number*10+1].value = "=B" + str((row_number)) + "+5.95"
    row_number += 1

    

    wks.update_cells(cell_list)

    print('Orders added to spreadsheet')
