import os
import sys
import datetime
import hashlib
from flask import redirect
from flask_httpauth import HTTPBasicAuth

# TODO: explicit import to understand better scope
from glideinmonitor.webserver.rest_api import *
from glideinmonitor.lib.config import config

app = Flask(__name__)
auth = HTTPBasicAuth()


#########################################
# Auth & Frontend HTML Router
#########################################

@auth.verify_password
def verify_password(username, password):
    if username in config.get('Users'):
        return config.get('Users').get(username) == hashlib.md5(password.encode()).hexdigest()
    return False


@app.route('/')
@auth.login_required
def app_homepage():
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'index.html'), 'r') as file:
        data = file.read()
    return data


@app.route('/job/<job_id>')
@auth.login_required
def app_job(job_id):
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'jobview.html'), 'r') as file:
        data = file.read()
    return data


@app.route('/job_guid_reroute/', methods=['POST'])
@auth.login_required
def app_job_guid():
    db = Database()
    if "GUID" in request.form:
        job_id = db.getDB_ID(request.form["GUID"])
        db.quit()
        if job_id is None:
            abort(404)
        return redirect("/job/" + str(job_id), code=303)

    abort(400)


@app.route('/assets/<name>')
@auth.login_required
def assets(name):
    return send_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', name))


@app.route('/assets/libs/<name>')
@auth.login_required
def assets_libs(name):
    return send_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'libs', name))


@app.errorhandler(404)
def page_not_found(e):
    return send_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', '404.html')), 404


#########################################
# REST API
#########################################

@app.route('/api/job_download/<job_guid>')
@auth.login_required
def flask_api_job_download(job_guid):
    # Download for job given GUID
    return send_file(api_job_file(job_guid, True), as_attachment=True)


@app.route('/api/job_download/db_id/<job_id>')
@auth.login_required
def flask_api_job_download_db(job_id):
    # Download for job given DB ID
    return send_file(api_job_file(job_id, False), as_attachment=True)


@app.route('/api/job_info/<job_guid>')
@auth.login_required
def flask_api_job_info(job_guid):
    # Info for a job given GUID
    return api_job_info(job_guid, True)


@app.route('/api/job_info/db_id/<job_id>')
@auth.login_required
def flask_api_job_info_db(job_id):
    # Info for a job given DB ID
    return api_job_info(job_id, False)


# Weird routing glitch w/ XHR requests - specify both forms
@app.route('/api/job_search/', methods=['POST'])
@app.route('/api/job_search', methods=['POST'])
@auth.login_required
def flask_api_job_search():
    return api_job_search()


@app.route('/api/entries')
@auth.login_required
def flask_api_entries():
    return api_entries()


# Redirect Flask output to log file
log_location_dir = os.path.join(config['Log_Dir'], 'server')
if not os.path.exists(log_location_dir):
    os.makedirs(log_location_dir)
log_location = os.path.join(log_location_dir, datetime.datetime.now().strftime("%Y-%m-%d") + ".txt")
sys.stderr = open(log_location, "a")
sys.stdout = open(log_location, "a")

# Start the Server
app.run(host=config.get('Host'), port=config.get('Port'))
