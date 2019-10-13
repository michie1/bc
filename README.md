# bc
Script that reads all orders of a topic from wtos.nl, puts everything in the basket of bike-components.de and generates a Google spreadsheet (https://wtos.nl/bc)

Put email/password/directory in config.py, see config.py-example.
Put bc number in state.json, see state.json.example
Ask Michiel for credentials.json, or create your own Google spreadsheet.

```
virtualenv -p python3 venv
source venv/bin/activate
pip install --upgrade -r requirements.txt
python main.py
```

