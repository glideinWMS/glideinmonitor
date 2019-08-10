import os

from flask import Flask, abort, send_file
from flask_httpauth import HTTPBasicAuth
from web_interface.web_homepage import homepage, genTable
from web_interface.web_jobview import jobview
from utils.database import Database
from config import config

app = Flask(__name__)
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if username in config.get('Users'):
        return config.get('Users').get(username) == password
    return False


@app.route('/')
@auth.login_required
def app_homepage():
    return homepage()


@app.route('/job/<job_id>')
@auth.login_required
def app_job_view(job_id):
    return jobview(job_id)


@app.route('/api/job_info/<job_id>')
@auth.login_required
def api_job_info(job_id):
    # Connect to the database (will setup if not existing)
    db = Database()

    path = db.getFile(job_id)

    db.quit()

    if path is None:
        abort(404)

    return send_file(path, as_attachment=True)


@app.route('/api/temp/')
@auth.login_required
def api_temp():
    return genTable()


@app.route('/api/jobs_on_date/<given_date>')
@auth.login_required
def api_jobs_on_date(given_date):
    return "API: JSON of Dates"


@app.route('/api/timeline')
@auth.login_required
def api_timeline():
    return "API: JSON of Dates"


@app.route('/assets/<name>')
@auth.login_required
def assets(name):
    return send_file(os.getcwd()+'\\web_interface\\assets\\'+name)


app.run()  # Start the Server
