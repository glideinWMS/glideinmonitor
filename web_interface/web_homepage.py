import os
import json

from utils.database import Database


def genTable():
    # Connect to the database (will setup if not existing)
    db = Database()

    table_raw = db.output_table()

    db.quit()

    return "{\"data\" :"+json.dumps(table_raw[:50])+"}"


def homepage():
    data = ""
    with open(os.getcwd() + '\\web_interface\\assets\\index.html', 'r') as file:
        data = file.read()
    return data
