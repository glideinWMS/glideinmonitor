import sqlite3
from config import config
from utils.logger import log


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(config['DB_Dir'] + '/database.sqlite')

        # Check if index table exists
        db_cursor = self.conn.cursor()
        db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_index';")

        if db_cursor.fetchone() is None:
            log("INFO", "Creating new database")

            # Table does not exist, add it
            script_file = open("databaseTableCreation.sql", 'r')
            script = script_file.read()
            script_file.close()
            db_cursor.executescript(script)

    def check_for_instance(self, job):
        # Checks if a job exists in the database
        cur = self.conn.cursor()

        # Do directory/file names need to be sanitized?
        cur.execute(
            "SELECT FrontendUsername, InstanceName, FileSize FROM file_index WHERE JobID='{}' and EntryName='{}'".format(
                job[0], job[3]))

        response = cur.fetchone()
        if response is None:
            return False
        else:
            if response[0] != job[1] or response[1] != job[2]:
                log("ERROR", "Duplicate job found for either another Frontend Username or an Instance Name")
                return False
            elif int(job[5] + job[7]) > int(response[2]):
                cur.execute("DELETE FROM file_index WHERE JobID='{}' and EntryName='{}'".format(job[0], job[3]))
                return False
            else:
                return True

    def add_job(self, job, path, found_logs):
        # Adds a job to the database

        # Insert into the database
        cur = self.conn.cursor()

        cur.execute(
            "INSERT INTO file_index(JobID, FileSize, Timestamp, FrontendUsername, InstanceName, EntryName, "
            "FilePath, "
            "MasterLog, StartdLog, StarterLog, StartdHistLog, XML_desc)"
            "VALUES('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')"
                .format(job[0], (job[5] + job[7]), job[8], job[1], job[2], job[3],
                        path,
                        found_logs[0], found_logs[1], found_logs[2], found_logs[3], found_logs[4]))
        return

    def commit(self):
        # Commits changes made to the database
        self.conn.commit()
        return

    def output_table(self):
        # Checks if a job exists in the database
        cur = self.conn.cursor()

        # Do directory/file names need to be sanitized?
        cur.execute("SELECT JobID, FileSize, Timestamp, FrontendUsername, InstanceName, EntryName, "
                    "MasterLog, StartdLog, StarterLog, StartdHistLog, XML_desc FROM file_index")

        return cur.fetchall()

    def getFile(self, jobID):
        # Checks if a job exists in the database
        cur = self.conn.cursor()

        # Do directory/file names need to be sanitized?
        cur.execute("SELECT FilePath FROM file_index WHERE ID='{}'".format(jobID))

        response = cur.fetchone()

        if response is None:
            return None
        else:
            return response[0]

    def quit(self):
        self.conn.close()
