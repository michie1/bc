import json
import gspread
import math
from oauth2client.service_account import ServiceAccountCredentials
import time
import pdb


def load_spreadsheet(bc_number):
    print 'Load Google credentials'
    json_key = json.load(open('credentials.json'))
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

    gc = gspread.authorize(credentials)
    sh = gc.open_by_key('1PgxD5wx6qrWtIfnJ89fdczpS6yKK5BOZZHcRQeZCnD4')

    sh.worksheets() # problem if this is removed
    sh.add_worksheet(title='0', rows='1', cols='1')


    try:
        # delete worksheet
        sh.del_worksheet(sh.worksheet("BC" + str(bc_number)))
    except gspread.exceptions.WorksheetNotFound as err:
        print err
        memcache.set("busy", "0")
    
    # make worksheet
    wks = sh.add_worksheet(title='BC' + str(bc_number), rows='200', cols='10')
    #wks = sh.worksheet('105_cart')

    sh.del_worksheet(sh.worksheet('0'))

    
    """
    header = wks.range('A1:J1')
    #header[0].value = 'besteller'
    #header[1].value = 'artikel'
    #header[2].value = 'type'
    #header[3].value = 'sku'
    header[4].value = 'Price alert'
    header[5].value = 'Originele prijs'
    header[6].value = 'Prijs per stuk'
    header[7].value = 'Aantal'
    header[8].value = 'Totaal'
    header[9].value = '5%'
    wks.update_cells(header)
    """

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

    #for user, products in orders.iteritems():
    for user, products in sorted(orders.iteritems()):

        #column_number = 0
        cell_list[row_number*10].value = user.decode('utf-8')
        row_number += 1
        first_row = row_number

        for product in products:
            if product == None:
                continue

            try:
                cell_list[row_number*10+0].value, cell_list[row_number*10+1].value = product['name'].decode('utf-8').split(' ', 1)
            except IndexError as e:
                print e
                print user, product
                print product['type']
                print row_number
                continue
            except KeyError as e:
                print e
                print user, product
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

        #try:
            #cell_list[row_number+8].value = '=SUM(I' + str(first_row) + ':I' + str(last_row) + ')'
            #cell_list[row_number+9].value = '=SUM(J' + str(first_row) + ':J' + str(last_row) + ')'
        #except gspread.exceptions.ConnectionError as err:
            #print err
            #memcache.set("busy", "0")

        row_number += 2
        print 'Order ' + user + ' prepared for spreadsheet'
        #time.sleep(1)

    wks.update_cells(cell_list)

    print 'Orders added to spreadsheet'

    #wks.update_cells(cell_list)

    """
    row_number = 2

    for user, products in orders.iteritems():
        wks.update_cell(row_number, 2, user.decode('utf-8'))
        row_number += 1
        first_row = row_number
        for product in products:
            print product
            row = wks.range('A' + str(row_number) + ':J' + str(row_number))
            row[0].value, row[1].value = product['name'].decode('utf-8').split(' ', 1)
            row[2].value = product['type']
            row[3].value = "=(\"" + product['sku'] + "\")"
            row[4].value = product['pa']
            row[5].value = product['original_price']
            row[6].value = product['price']
            row[7].value = product['qty']
            row[8].value = "=G" + str(row_number) + "*H" + str(row_number)
            row[9].value = "=CEILING(I" + str(row_number) + "*0.95, 0.01)"
            #row[8].value = float(product['price']) * product['qty']
            #row[9].value = math.ceil(float(row[5].value) * 0.95 * 100) / 100

            wks.update_cells(row)
            row_number += 1
        last_row = row_number - 1
        try:
            wks.update_cell(row_number, 9, '=SUM(I' + str(first_row) + ':I' + str(last_row) + ')')
            #wks.update_cell(row_number, 10, '=CEILING(I' + str(row_number) + '*0.95, 0.01)')
            wks.update_cell(row_number, 10, '=SUM(J' + str(first_row) + ':J' + str(last_row) + ')')
        except gspread.exceptions.ConnectionError as err:
            print err
            memcache.set("busy", "0")

        row_number += 2
        print 'Order ' + user + ' in spreadsheet'
        time.sleep(1)

    print 'Orders added to spreadsheet'
    """

