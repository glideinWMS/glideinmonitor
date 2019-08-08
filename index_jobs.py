import os
import datetime
import tarfile
from database import Database
from config import config
from logger import log
import mmap


def directory_tree(start_path):
    tree = []

    frontend_username = ""
    instance_name = ""
    entry_name = ""

    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)

        if level == 2:
            frontend_username = os.path.basename(root)

        if level == 3:
            instance_name = os.path.basename(root)

        if level == 4:
            entry_name = os.path.basename(root)

        for f in files:
            if (os.path.splitext(f)[1] == ".out") or (os.path.splitext(f)[1] == ".err"):
                f_path = os.path.join(root, f)

                f_size = os.path.getsize(f_path)

                tree.append([f, frontend_username, instance_name, entry_name, f_size, f_path])

    return tree


def begin_indexing():
    save_dir = config['Saved_Log_Dir'] + "/" + datetime.datetime.now().strftime("/%Y-%m-%d")
    tree_unorganized = directory_tree(config['GWMS_Log_Dir'])
    tree_organized = {}
    jobs_added = 0

    # Organize the tree where the output and error file are together
    job_count_complete = 0
    for curr_inst in tree_unorganized:
        frontend_user = curr_inst[1]
        instance_name = curr_inst[2]
        entry_name = curr_inst[3]
        job_id = os.path.splitext(curr_inst[0])[0]
        job_type = os.path.splitext(curr_inst[0])[1]

        if (entry_name, job_id) in tree_organized:
            if job_type == ".out":
                tree_organized[(entry_name, job_id)][4] = curr_inst[5]
                tree_organized[(entry_name, job_id)][5] = curr_inst[4]
            else:
                tree_organized[(entry_name, job_id)][6] = curr_inst[5]
                tree_organized[(entry_name, job_id)][7] = curr_inst[4]
            job_count_complete += 1
        else:
            if job_type == ".out":
                tree_organized[(entry_name, job_id)] = [job_id, frontend_user, instance_name, entry_name,
                                                        curr_inst[5], curr_inst[4], None, None]
            else:
                tree_organized[(entry_name, job_id)] = [job_id, frontend_user, instance_name, entry_name,
                                                        None, None, curr_inst[5], curr_inst[4]]

    # Issue a warning if an output file doesn't have a error (or vise-versa)
    if job_count_complete * 2 != len(tree_unorganized):
        log("ERROR", "Organizing the tree, job is either duplicated where it shouldn't or missing"
                     " (Counted {} Processed {})".format(len(tree_unorganized), job_count_complete*2))

    # Connect to the database (will setup if not existing)
    db = Database()

    # Iterate through each job checking the database if it needs to be updated
    for job_name, job_data in tree_organized.items():
        # Check if the current instance is in the database, if not then add it
        # found_logs = [False, False, False, False, False]
        if not (db.check_for_instance(job_data)):
            # Create the directory if it does not exist
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # Check if the file has certain logs within it
            found_logs = [False, False, False, False, False]
            if job_data[7] != 0:
                if job_data[6] is None:
                    log("WARNING", "Job "+str(job_data[0])+" does not have an error file, skipping")
                    continue

                with open(job_data[6], 'rb', 0) as file, \
                        mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                    if s.find(b'MasterLog\n========') != -1:
                        found_logs[0] = True
                    if s.find(b'StartdLog\n========') != -1:
                        found_logs[1] = True
                    if s.find(b'StarterLog\n========') != -1:
                        found_logs[2] = True
                    if s.find(b'StartdHistoryLog\n========') != -1:
                        found_logs[3] = True
                    if s.find(b'=== Encoded XML description of glidein activity ===') != -1:
                        found_logs[4] = True

            # Tar the output and error file
            curr_job_path = save_dir + "/" + job_name[0] + "_" + job_name[1] + ".tar.gz"
            with tarfile.open(curr_job_path, "w:gz") as tar:
                tar.add(job_data[4], arcname=os.path.basename(job_data[4]))
                tar.add(job_data[6], arcname=os.path.basename(job_data[6]))
                tar.close()

            # Add it to the database
            db.add_job(job_data, curr_job_path, found_logs)

            jobs_added += 1

    # Indexing Complete
    db.commit()
    log("INFO", "Jobs added/updated " + str(jobs_added))


begin_indexing()
