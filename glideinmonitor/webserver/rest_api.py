from flask import Flask, abort, send_file, request
import json

from glideinmonitor.lib.database import *
from glideinmonitor.lib.config import Config


def api_job_file(job_id, given_guid):
    # Get configuration
    file_type = Config.get('DisplayType')

    # Sends the job file itself
    db = Database()
    path = db.getFile(job_id, given_guid, file_type)
    db.quit()

    # If it's not found, send a 404
    if path is None:
        abort(404)

    return path


def api_job_info(job_id, given_guid):
    # Provides info on a job in a JSON format
    db = Database()
    data = db.getInfo(job_id, given_guid)
    db.quit()

    # If it's not found, send a 404
    if data is None:
        abort(404)

    return json.dumps(data)


def api_job_search():
    # Returns list of jobs given timestamp (from,to) and entry name(s) up to 50k
    if request.method == 'POST':
        db = Database()

        timestamp_from = None
        timestamp_to = None
        entries = None

        if "timestamp_from" in request.form:
            try:
                timestamp_from = int(request.form["timestamp_from"])
            except ValueError:
                pass

        if "timestamp_to" in request.form:
            try:
                timestamp_to = int(request.form["timestamp_to"])
            except ValueError:
                pass

        if "entries" in request.form:
            # Get a list of entries for sanitation later
            entries_list = db.known_entries()

            try:
                # Try to turn the JSON into a list
                given_list = json.loads(request.form["entries"])

                # Check to make sure entries sent are valid
                entries = []
                for x in given_list:
                    if x in entries_list:
                        entries.append(x)

            except json.decoder.JSONDecodeError:
                pass

        # Returns list of entries found in the database
        table_raw = db.output_table(timestamp_from, timestamp_to, entries)

        db.quit()

        # "data": needed for js tables
        return "{\"data\" :" + json.dumps(table_raw) + "}"


def api_entries():
    # Returns list of entries found in the database
    db = Database()
    entries_list = db.known_entries()
    db.quit()

    return json.dumps(entries_list)
