import datetime
import mmap
import os
import tarfile
import time
import pathlib

from utils.config import config
from utils.database import Database
from utils.logger import log


def current_milli_time():
    return lambda: int(round(time.time() * 1000))


def directory_jobs(start_path):
    # Allowed file types
    allowed_types = [".out", ".err"]

    # This will include every job that is currently found on the disk
    tree = {}

    # The path tells some information inherited about the job
    path_frontend_username = ""
    path_instance_name = ""
    path_entry_name = ""

    # Some files don't have a timestamp in it's .err file,
    #   use the one from the previous job if it's not there
    last_known_timestamp = 0

    # Iterate through each folder in the starting directory (probably GWMS_Log_Dir)
    for root, dirs, files in os.walk(start_path):
        # Child directory level
        level = root.replace(start_path, '').count(os.sep)

        # This child directory represents a frontend username
        if level == 2:
            path_frontend_username = os.path.basename(root)

        # This child directory represents an instance name
        if level == 3:
            path_instance_name = os.path.basename(root)

        # This child directory represents an entry name
        if level == 4:
            # Reset each timestamp when it moves from one entry to another
            last_known_timestamp = 0
            path_entry_name = os.path.basename(root)

        # File found, check if it's a file we should focus on
        for f in files:
            file_type = os.path.splitext(f)[1]

            if file_type in allowed_types:
                # Info that can be grabbed immediately w/out opening file
                file_path = os.path.join(root, f)
                file_size = os.path.getsize(file_path)
                job_id = os.path.splitext(f)[0]
                job_type = file_type

                # GUID by default is FrontendUsername@InstanceName@EntryName@JobID
                guid = path_frontend_username + "@" + path_instance_name + "@" + path_entry_name + "@" + job_id

                # Try and get out specific information
                if job_type == ".out":
                    with open(file_path) as f:
                        # Get timestamp (should be first line)
                        first_line = f.readline()
                        try:
                            last_known_timestamp = int(first_line.split('(', 1)[1].split(')')[0])
                        except IndexError:
                            pass

                        # Get the GUID (should be second line)
                        second_line = f.readline()
                        try:
                            guid = second_line.split('(', 1)[1].split(')')[0]
                        except IndexError:
                            pass

                # Now add the job to the tree, use it's (entry name, job id) to place it uniquely in the tree
                if (path_entry_name, job_id) not in tree:
                    tree[(path_entry_name, job_id)] = {}
                    tree[(path_entry_name, job_id)]["job_id"] = job_id
                    tree[(path_entry_name, job_id)]["frontend_user"] = path_frontend_username
                    tree[(path_entry_name, job_id)]["instance_name"] = path_instance_name
                    tree[(path_entry_name, job_id)]["entry_name"] = path_entry_name

                # Add file type specific data
                if job_type == ".out":
                    tree[(path_entry_name, job_id)]["out_file_path"] = file_path
                    tree[(path_entry_name, job_id)]["out_file_size"] = file_size
                    tree[(path_entry_name, job_id)]["timestamp"] = last_known_timestamp
                    tree[(path_entry_name, job_id)]["guid"] = guid
                elif job_type == ".err":
                    tree[(path_entry_name, job_id)]["err_file_path"] = file_path
                    tree[(path_entry_name, job_id)]["err_file_size"] = file_size
    return tree


def begin_indexing():
    # Check for index job lock
    lock_location = os.path.join(config['Saved_Log_Dir'], "index_lock")
    if not pathlib.Path(lock_location).exists():
        pathlib.Path(lock_location).touch()
    else:
        # Job index already running/did not complete
        log("ERROR", "Lock file present in saved log directory")
        return

    # Entry point for indexing
    db = Database()
    jobs_updated = 0
    save_dir = config['Saved_Log_Dir'] + "/" + datetime.datetime.now().strftime("/%Y-%m-%d")
    log("INFO", "Begin Indexing Time Time: " + str(current_milli_time()))

    # Get a dictionary of jobs from the GWMS_Log_Dir directory
    tree = directory_jobs(config['GWMS_Log_Dir'])

    log("INFO", "Directory Listing Completion Time: " + str(current_milli_time()))

    # Iterate through each job checking the database if it needs to be updated
    for job_name, job_data in tree.items():
        # Skip entries that are missing an err/out file
        if "err_file_path" not in job_data or "out_file_path" not in job_data:
            log("INFO", "Missing ERR/OUT file for entry - jobID: " +
                job_data["entry_name"] + " - " + str(job_data["job_id"]))
            continue

        # Check if the current instance is in the database, if not then add it
        if db.needs_update(job_data):
            # Create the directory if it does not exist
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # Check if the file has certain logs within it
            found_logs = {"MasterLog": False, "StartdLog": False, "StarterLog": False,
                          "StartdHistoryLog": False, "glidein_activity": False}
            if job_data['err_file_size'] != 0:
                with open(job_data["err_file_path"], 'rb', 0) as file, \
                        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                    if s.find(b'MasterLog\n========') != -1:
                        found_logs["MasterLog"] = True
                    if s.find(b'StartdLog\n========') != -1:
                        found_logs["StartdLog"] = True
                    if s.find(b'StarterLog\n========') != -1:
                        found_logs["StarterLog"] = True
                    if s.find(b'StartdHistoryLog\n========') != -1:
                        found_logs["StartdHistoryLog"] = True
                    if s.find(b'=== Encoded XML description of glidein activity ===') != -1:
                        found_logs["glidein_activity"] = True

            # Tar the output and error file
            curr_job_path = save_dir + "/" + job_name[0] + "_" + job_name[1] + ".tar.gz"
            with tarfile.open(curr_job_path, "w:gz") as tar:
                tar.add(job_data["out_file_path"], arcname=os.path.basename(job_data["out_file_path"]))
                tar.add(job_data["err_file_path"], arcname=os.path.basename(job_data["err_file_path"]))
                tar.close()

            # Add/Update it in the database
            db.add_job(job_data, curr_job_path, found_logs)

            # Job added/updated
            jobs_updated += 1

    # Indexing complete
    db.commit()

    # Delete the lock file
    os.remove(pathlib.Path(lock_location))

    log("INFO", "Jobs added/updated " + str(jobs_updated))
    log("INFO", "Indexing Complete Time: " + str(current_milli_time()))


begin_indexing()
