from flask import Flask, abort, send_file
from web_homepage import homepage
from web_jobview import jobview
from database import Database

app = Flask(__name__)


@app.route('/')
def app_homepage():
    return homepage()


@app.route('/job/<job_id>')
def app_job_view(job_id):
    return jobview(job_id)


@app.route('/api/job_info/<job_id>')
def api_job_info(job_id):
    # Connect to the database (will setup if not existing)
    db = Database()

    path = db.getFile(job_id)

    db.quit()

    if path is None:
        abort(404)

    return send_file(path, as_attachment=True)


@app.route('/api/jobs_on_date/<given_date>')
def api_jobs_on_date(given_date):
    return "API: JSON of Dates"


@app.route('/api/timeline')
def api_timeline():
    return "API: JSON of Dates"


@app.route('/assets/<name>')
def assets(name):
    return send_file('assets/'+name)


app.run()  # Start the Server
