import os
import sqlite3
MYSQL_AVAILABLE = True
try:
    import mysql.connector
except ImportError:
    MYSQL_AVAILABLE = False

from glideinmonitor.lib.config import Config
from glideinmonitor.lib.logger import log


class Database:
    def __init__(self):
        # Connect to SQLite unless specified otherwise in the config file
        if Config.db("type") == "sqlite":
            # SQLite Database
            try:
                os.mkdir(Config.db("dir"))
                log("INFO", "Creating new directory for SQLite DB")
            except FileExistsError:
                pass
            self.conn = sqlite3.connect(os.path.join(Config.db("dir"), "%s.sqlite" % Config.db("db_name")))

            # Check if index table exists
            db_cursor = self.conn.cursor()
            db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_index';")

            if db_cursor.fetchone() is None:
                # It doesn't, create it
                log("INFO", "Creating new SQLite database")

                script_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "sqliteTableCreation.sql"),
                                   'r')
                script = script_file.read()
                script_file.close()
                db_cursor.executescript(script)
        elif Config.db("type") == "mysql":
            # MySQL Database
            if not MYSQL_AVAILABLE:
                log("ERROR", "MySQL database selected but there is no MySQL connector")
                raise ImportError("Module not found: mysql.connector")
            try:
                self.conn = mysql.connector.connect(
                    host=Config.db("host"),
                    user=Config.db("user"),
                    passwd=Config.db("pass"),
                    database=Config.db("db_name")
                )

                mycursor = self.conn.cursor()
            except mysql.connector.errors.ProgrammingError:
                # Create the database
                log("INFO", "Creating new MySQL Database")
                mydb = mysql.connector.connect(
                    host=Config.db("host"),
                    user=Config.db("user"),
                    passwd=Config.db("pass")
                )

                mycursor = mydb.cursor()
                mycursor.execute("CREATE DATABASE " + Config.db("db_name"))

                self.conn = mysql.connector.connect(
                    host=Config.db("host"),
                    user=Config.db("user"),
                    passwd=Config.db("pass"),
                    database=Config.db("db_name")
                )

                mycursor = self.conn.cursor()

            # Check if the table exists
            mycursor.execute("SHOW TABLES")

            if ('file_index',) not in mycursor:
                # Create table
                log("INFO", "Creating MySQL File Index table")
                script_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "mysqlTableCreation.sql"),
                                   'r')
                script = script_file.read()
                script_file.close()
                mycursor.execute(script)
        else:
            log("ERROR", "No valid database selected (%s)" % Config.db("type"))
            raise ImportError("Invalid ")

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def needs_update(self, job):
        # Checks if a job exists in the database and if it needs updating
        cur = self.conn.cursor()

        # Do directory/file names need to be sanitized?
        cur.execute(
            "SELECT FrontendUsername, InstanceName, FileSize FROM file_index WHERE JobID='{}' and EntryName='{}'".format(
                job["job_id"], job["entry_name"]))

        response = cur.fetchone()
        if response is None:
            # Does not exist in db
            return True
        else:
            # Does exist in db
            if response[0] != job["frontend_user"] or response[1] != job["instance_name"]:
                log("ERROR", "Duplicate job found for either another Frontend Username or an Instance Name")
                return TabError
            elif int(job["err_file_size"] + job["out_file_size"]) > int(response[2]):
                # File size is greater, therefore update the job
                return True
            else:
                # Already added without a file size difference
                return False

    def add_job(self, job, path_original, path_filter):
        # Adds a job to the database

        cur = self.conn.cursor()

        # Escape the path (MySQL only)
        try:
            path_original = self.conn.converter.escape(path_original)
            path_filter = self.conn.converter.escape(path_filter)
        except AttributeError:
            pass

        # Check if the job is in the database already
        cur.execute(
            "SELECT FrontendUsername, FileSize FROM file_index WHERE JobID='{}' and EntryName='{}' and InstanceName='{}'"
                .format(job["job_id"], job["entry_name"], job["instance_name"]))

        response = cur.fetchone()
        if response is None:
            # Does not exist in db, insert it
            cur.execute(
                "INSERT INTO file_index(JobID, GUID, FileSize, Timestamp, FrontendUsername, InstanceName, EntryName, "
                "FilePathOriginal, FilePathFilter, "
                "MasterLog, StartdLog, StarterLog, StartdHistLog, XML_desc)"
                "VALUES('{}','{}' , '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                    job["job_id"], job["guid"], (job["out_file_size"] + job["err_file_size"]), job["timestamp"],
                    job["frontend_user"], job["instance_name"], job["entry_name"], path_original, path_filter,
                    job["MasterLog"], job["StartdLog"], job["StarterLog"],
                    job["StartdHistoryLog"], job["glidein_activity"]))
        else:
            # Job already exists, then update it
            cur.execute(
                "UPDATE file_index SET FilePathOriginal = '{}', FilePathFilter = '{}', FileSize = '{}', MasterLog = '{}', StartdLog = '{}',"
                "StarterLog = '{}', StartdHistLog = '{}', XML_desc = '{}' WHERE GUID = '{}' AND "
                "FrontendUsername = '{}' AND InstanceName = '{}' AND EntryName = '{}' AND Timestamp = '{}' "
                "AND JobID = '{}'".format(
                    path_original, path_filter, (job["out_file_size"] + job["err_file_size"]), job["MasterLog"],
                    job["StartdLog"], job["StarterLog"], job["StartdHistoryLog"],
                    job["glidein_activity"], job["guid"], job["frontend_user"], job["instance_name"],
                    job["entry_name"], job["timestamp"], job["job_id"]
                ))
        return

    def commit(self):
        # Commits changes made to the database
        self.conn.commit()
        return

    def output_table(self, timestamp_from, timestamp_to, entries):
        # Table output for the homepage
        cur = self.conn.cursor()

        where_stm = ""

        if timestamp_from is not None:
            if where_stm != "":
                where_stm += " AND "

            where_stm += "Timestamp >= " + str(timestamp_from)

        if timestamp_to is not None:
            if where_stm != "":
                where_stm += " AND "

            where_stm += "Timestamp <= " + str(timestamp_to)

        if entries is not None:
            if where_stm != "":
                where_stm += " AND "

            where_stm += "EntryName IN ("

            comma = 0
            for entry in entries:
                if comma == 1:
                    where_stm += ','

                where_stm += '"' + entry + '"'
                comma = 1

            where_stm += ") "

        if where_stm != "":
            where_stm = " WHERE " + where_stm

        sql = "SELECT ID, JobID, FileSize, Timestamp, FrontendUsername, InstanceName, EntryName, MasterLog, StartdLog, StarterLog, StartdHistLog, XML_desc FROM file_index " + where_stm + " LIMIT 50000"

        cur.execute(sql)

        return cur.fetchall()

    def known_entries(self):
        # List all known entry names for API
        cur = self.conn.cursor()

        cur.execute("SELECT DISTINCT EntryName FROM file_index LIMIT 50000")

        output = cur.fetchall()
        entries = [i[0] for i in output]

        return entries

    def getFile(self, jobID, given_guid, type):
        # Checks if a job exists in the database
        cur = self.conn.cursor()

        if type == 'original':
            # Do directory/file names need to be sanitized?
            if given_guid:
                cur.execute("SELECT FilePathOriginal FROM file_index WHERE GUID='{}'".format(jobID))
            else:
                cur.execute("SELECT FilePathOriginal FROM file_index WHERE ID='{}'".format(jobID))
        else:
            # Do directory/file names need to be sanitized?
            if given_guid:
                cur.execute("SELECT FilePathFilter FROM file_index WHERE GUID='{}'".format(jobID))
            else:
                cur.execute("SELECT FilePathFilter FROM file_index WHERE ID='{}'".format(jobID))

        response = cur.fetchone()

        if response is None:
            return None
        else:
            return response[0]

    def getInfo(self, jobID, given_guid):
        # Checks if a job exists in the database
        try:
            cur = self.conn.cursor(dictionary=True)
        except TypeError:
            cur = self.conn.cursor()

        cur.row_factory = self.dict_factory

        # Do directory/file names need to be sanitized?
        if given_guid:
            cur.execute("SELECT * FROM file_index WHERE GUID LIKE '{}'".format(jobID))
        else:
            cur.execute("SELECT * FROM file_index WHERE ID='{}'".format(jobID))

        response = cur.fetchone()

        if response is None:
            return None
        else:
            return response

    def getDB_ID(self, guidID):
        # Get's DB ID from GUID
        cur = self.conn.cursor()

        # Do directory/file names need to be sanitized?
        cur.execute("SELECT ID FROM file_index WHERE GUID='{}'".format(guidID))

        response = cur.fetchone()

        if response is None:
            return None
        else:
            return response[0]

    def quit(self):
        self.conn.close()
