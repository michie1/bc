import gspread

def write_spreadsheet():
   print 'write spreadsheet' 
   url = 'https://docs.google.com/spreadsheets/d/1PgxD5wx6qrWtIfnJ89fdczpS6yKK5BOZZHcRQeZCnD4/edit#gid=0'
   gc = gspread.authorize(credentials)
   sht2 = gc.open_by_url('1PgxD5wx6qrWtIfnJ89fdczpS6yKK5BOZZHcRQeZCnD4')



