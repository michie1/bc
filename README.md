# bc

Script that reads all orders of a topic from wtos.nl, puts everything in the basket of bike-components.de and generates a Google spreadsheet (https://wtos.nl/bc)

## Development

To install and work on bc locally:

```bash
git clone https://github.com/michie1/bc.git
cd bc
virtualenv -p python3 venv
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Configuration

Fill in the credentials of config.py, see config.py-example.
Put the current bc order number in state.json, see state.json.example.
There are 3 options:
1) Ask Michiel for credentials.json
2) Create your own Google spreadsheet (see below)
3) Copy credentials-example.json and visit (http://wtos.nl/bc?test) for the spreadsheet. This is the most easy option for testing and starting working on this project, but this one is shared with multiple people. The spreadsheet key is already set in the example.

### Run the program

```bash
source venv/bin/activate
python main.py
```

## Create your own Google spreadsheet

This application uses the Google spreadsheets API via [gspread](https://github.com/burnash/gspread/).
Signed credentials are needed to access your own spreadsheets.
gspread uses a service account key.

1. Go to [Google Developer Console](https://console.developers.google.com) and create a new project.

2. Under "API and services", search for the "Google Sheets API" and enable.

3. Go to "Credentials" and select "Create credentials" -> "Service account key".

4. Select new service account and fill in a name. You don't have to specify a role. Select JSON as the key type.

5. Save the downloaded file as credentials.json in the main folder.

6. You will need the _client_email_ from this file. In Google drive create the spreadsheet you want to use. Share this spreadsheet with the _client_email_. In this way you authorise access to the spreadsheet. If you forget to do this, you will get a  ``SpreadhsheetNotFound`` exception when trying to access this spreadsheet.

7. Retrieve the spreadsheet key from the spreadsheet url and add it to config.py.

You are now ready to run the program.
