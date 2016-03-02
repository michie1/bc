import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def load_spreadsheet():
    print 'Load Google credentials'
    json_key = json.load(open('credentials.json'))
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

    gc = gspread.authorize(credentials)
    sh = gc.open_by_key('1PgxD5wx6qrWtIfnJ89fdczpS6yKK5BOZZHcRQeZCnD4')

    # delete worksheet
    sh.del_worksheet(sh.worksheet('105_cart'))

    # make worksheet
    wks = sh.add_worksheet(title="105_cart", rows='100', cols='10')
    #wks = sh.worksheet('105_cart')

    
    header = wks.range('A1:E1')
    header[0].value = 'besteller'
    header[1].value = 'artikel'
    header[2].value = 'type'
    header[3].value = 'aantal'
    header[4].value = 'price alert'
    wks.update_cells(header)

    return wks

def add_spreadsheet(orders):
    print orders

    print 'Orders added to spreadsheet'

def write_summary():
    print 'write summary'


