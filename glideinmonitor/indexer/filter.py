import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import time
import uuid

from queue import Queue
from threading import Thread

from glideinmonitor.lib.config import Config
from glideinmonitor.lib.logger import log
from glideinmonitor.lib import condor_conversion


class FilterInstance:
    name = ""
    exe_full_path = ""
    exe_timeout = 0
    type = ""
    input_directory = ""
    output_directory = ""
    status = False

    exe_subprocess = None

    def __init__(self, name, exe_path, filter_type, timeout, base_filter_dir):
        # Save known info
        self.exe_full_path = exe_path
        self.type = filter_type
        self.exe_timeout = timeout
        self.name = name

        # Create input/output directories
        base_instance_dir = os.path.join(base_filter_dir, hashlib.md5(name.encode('utf-8')).hexdigest())
        self.input_directory = os.path.join(base_instance_dir, 'input')
        self.output_directory = os.path.join(base_instance_dir, 'output')

        os.makedirs(self.input_directory, exist_ok=True)
        os.makedirs(self.output_directory, exist_ok=True)

    def is_running(self):
        # Returns if the current instance of the filter is running
        return self.status


class Filter:
    instance_list = []
    status = False  # If any filters are currently running
    filter_base_dir = None
    timeout_start = None

    filterRunner = None
    jobQueue = None
    messageQueue = None

    def __init__(self):
        # Load the configuration for the filters
        try:
            filter_list_from_config = Config.filters()
        except Exception as e:
            log("ERROR", "Filter configuration error: " + str(e))
            sys.exit()  # Configuration errors should prevent execution

        # Create (and empty if needed) base filter path
        self.filter_base_dir = os.path.join(Config.get('Saved_Log_Dir'), 'temp_filter_processing')
        if os.path.isdir(self.filter_base_dir):
            shutil.rmtree(self.filter_base_dir)

        # Create staging (all original files go here) and final (all filtered files end up here) directories
        os.makedirs(os.path.join(self.filter_base_dir, 'staging'), exist_ok=True)
        os.makedirs(os.path.join(self.filter_base_dir, 'final'), exist_ok=True)

        # Build the filter instance list
        for filter_from_config in filter_list_from_config:
            self.instance_list.append(FilterInstance(
                filter_from_config.get("name"),
                filter_from_config.get("exe"),
                filter_from_config.get("type"),
                filter_from_config.get("timeout"),
                self.filter_base_dir
            ))

        log("INFO", str(len(filter_list_from_config)) + " valid filters have been found")

    @staticmethod
    def move_files(input_dir, output_dir):
        # Moves any files from one directory to another, returning true if it moved files
        moved_files = False
        input_dir_files = [file
                           for file in os.listdir(input_dir)
                           if os.path.isfile(os.path.join(input_dir, file))]

        for file in input_dir_files:
            moved_files = True
            shutil.move(os.path.join(input_dir, file), output_dir)

        return moved_files

    @staticmethod
    def dir_empty_check(input_dir):
        if len(os.listdir(input_dir)) == 0:
            return False
        else:
            return True

    @staticmethod
    def type_moving(input_dir, output_dir, end_type, unpacked_expectations):
        # Convert & move files from one directory to another, returning true if it moved files
        moved_files = False

        input_dir_files = [file
                           for file in os.listdir(input_dir)
                           if os.path.isfile(os.path.join(input_dir, file))]

        for file in input_dir_files:
            current_file_uuid = os.path.splitext(file)[0]

            if os.path.splitext(file)[1] == '.out':
                # Move the file if it's an .out file
                moved_files = True
                shutil.move(os.path.join(input_dir, file), output_dir)
            else:
                # Convert the .err file
                if end_type == "whole":
                    # Only process .err files (any other extension ignore)
                    if os.path.splitext(file)[1] != '.err':
                        continue

                    # Now check if all the files are present for the rebuild of the .err file
                    all_files_present = True
                    if current_file_uuid in unpacked_expectations:
                        for unpacked_file in unpacked_expectations[current_file_uuid]:
                            if unpacked_file not in input_dir_files:
                                all_files_present = False
                                break
                    if not all_files_present:
                        continue

                    # At this point, all necessary .err.NAME files are present, rebuild the .err file
                    moved_files = True
                    condor_conversion.unpacked_to_whole(current_file_uuid, input_dir, output_dir)
                else:
                    # Only expecting a '.err' file - process that
                    moved_files = True
                    unpacked_extras = condor_conversion.whole_to_unpacked(current_file_uuid, input_dir, output_dir)
                    unpacked_expectations[current_file_uuid] = unpacked_extras

        return moved_files, unpacked_expectations

    @staticmethod
    def filter_runner(base_directory, instance_list, job_queue, messageQueue):
        # Variables within runner
        master_jobs_list = {}
        unpacked_expectations = {}

        staging_dir = os.path.join(base_directory, 'staging')
        final_dir = os.path.join(base_directory, 'final')

        timeout_stepper = 0
        timeout_start = None
        completion_check = False

        # The thread runner method, runs until cleanup method
        while len(instance_list) != 0:
            # Check for messages
            for i in range(0, messageQueue.qsize()):
                # Get the message
                the_message = messageQueue.get()

                # Check for timeout
                if the_message == 'TIMEOUT_START':
                    # Timeout received
                    timeout_start = time.time()

            # Should this pass check for completion
            if timeout_start:
                completion_check = True

            # Process any new jobs
            for i in range(0, job_queue.qsize()):
                # Get the next job passed from the indexer
                completion_check = False
                next_job = job_queue.get()

                # Generate a unique ID for the job
                job_uuid = str(uuid.uuid1())
                while job_uuid in master_jobs_list:
                    job_uuid = uuid.uuid1()

                # Add it to the list (used at the end to build the archive
                # (Archive path, .out file name, .err file name)
                master_jobs_list[job_uuid] = (next_job[0],
                                              os.path.basename(next_job[1]["out_file_path"]),
                                              os.path.basename(next_job[1]["err_file_path"]))

                # New job, move all files to the staging directory
                shutil.copyfile(next_job[1]['err_file_path'], os.path.join(staging_dir, job_uuid + '.err'))
                shutil.copyfile(next_job[1]['out_file_path'], os.path.join(staging_dir, job_uuid + '.out'))

            # Go through each filter from the top**, moving files as necessary
            for i in range(len(instance_list)):
                # Check for new files and move/convert if needed depending on the type
                if i == 0:
                    # Check the staging directory if it's on the first filter
                    if instance_list[i].type == 'whole':
                        new_files = Filter.move_files(staging_dir, instance_list[i].input_directory)
                    else:
                        new_files, updating_expectations = Filter.type_moving(staging_dir,
                                                                              instance_list[i].input_directory,
                                                                              instance_list[i].type,
                                                                              unpacked_expectations)
                        unpacked_expectations.update(updating_expectations)
                else:
                    if instance_list[i].type == instance_list[i - 1].type:
                        new_files = Filter.move_files(instance_list[i - 1].output_directory,
                                                      instance_list[i].input_directory)
                    else:
                        new_files, updating_expectations = Filter.type_moving(instance_list[i - 1].output_directory,
                                                                              instance_list[i].input_directory,
                                                                              instance_list[i].type,
                                                                              unpacked_expectations)
                        unpacked_expectations.update(updating_expectations)

                # If it didn't move any files, check if there are any files still in the input directory
                if not new_files:
                    new_files = Filter.dir_empty_check(instance_list[i].input_directory)

                # Start the filter executable if not already running only if there are new files
                if new_files:
                    completion_check = False

                    # Timeout check
                    if timeout_start is not None and timeout_stepper == i:
                        # The timeout has already started and current waiting on this filter
                        # Check if it needs to stop this filter
                        curr_filter_timeout = instance_list[i].exe_timeout
                        if time.time() - timeout_start > curr_filter_timeout != 0:
                            # Stopping this process if needed and deleting files from it's input directory
                            print("Timeout reached")
                            instance_list[i].exe_subprocess.terminate()

                            for root, dirs, files in os.walk(instance_list[i].input_directory):
                                for f in files:
                                    os.remove(os.path.join(root, f))

                            log("ERROR", "Filter \"" + instance_list[i].name + "\" timeout reached")

                    if instance_list[i].exe_subprocess is None or instance_list[i].exe_subprocess.poll() is not None:
                        # If the filter did run, check the return code
                        if instance_list[i].exe_subprocess is not None:
                            # Get the return code
                            return_code_from_filter_exe = instance_list[i].exe_subprocess.poll()

                            # Check if the return code signals a failure
                            if return_code_from_filter_exe != 0:
                                # The filter exe errored out, submit the error to the log and terminate filters running
                                log("ERROR", "The filter \"" + instance_list[i].name +
                                    "\" encountered a return code of: " + str(return_code_from_filter_exe) +
                                    "\nTherefore the filters have been terminated, no filter archive created.")
                                return

                        # Start the exe of the filter instance with the appropriate arguments
                        instance_list[i].exe_subprocess = subprocess.Popen([instance_list[i].exe_full_path,
                                                                            "-i", instance_list[i].input_directory,
                                                                            "-o", instance_list[i].output_directory])
                else:
                    # Check if the timeout was waiting on this filter
                    if timeout_start is not None and timeout_stepper == i:
                        # It was waiting on this filter, and it finished processing files - move to the next filter
                        timeout_stepper += 1
                        timeout_start = time.time()

            # Check the last filter's output folder and move any files to the final directory
            if instance_list[len(instance_list) - 1].type == 'whole':
                new_files = Filter.move_files(instance_list[len(instance_list) - 1].output_directory, final_dir)
            else:
                new_files, updating_expectations = new_files = Filter.type_moving(
                    instance_list[len(instance_list) - 1].output_directory,
                    final_dir, 'whole', unpacked_expectations)
                unpacked_expectations.update(updating_expectations)

            if new_files:
                # New files, package them if both the .err and .out available
                # Currently, jobs getting to the beginning of the filtering stage will have both .err and .out

                # List all files in the final directory
                final_dir_files = [file
                                   for file in os.listdir(final_dir)
                                   if os.path.isfile(os.path.join(final_dir, file))]

                final_dir_jobs = []
                # Create a list containing complete jobs
                for file in final_dir_files:
                    #  Get the current file's uuid and extension
                    job_uuid, curr_ext = os.path.splitext(file)

                    # Check if the file's job has already been added
                    if job_uuid in final_dir_jobs:
                        continue

                    # Get the other job extension (if the current file is a .out, the other is .err and vice versa)
                    other_ext = '.out'
                    if curr_ext == '.out':
                        other_ext = '.err'

                    # Check if the other file is in the folder
                    if job_uuid + other_ext in final_dir_files:
                        # By far, the most efficient way to program this - Thomas Hein, programmer of the year here
                        final_dir_jobs.append(job_uuid)

                # For all complete jobs, archive them
                for completed_job_uuid in final_dir_jobs:
                    # Save the original immediately
                    with tarfile.open(master_jobs_list[completed_job_uuid][0], "w:gz") as tar:
                        tar.add(os.path.join(final_dir, completed_job_uuid + ".out"),
                                arcname=os.path.basename(master_jobs_list[completed_job_uuid][1]))
                        tar.add(os.path.join(final_dir, completed_job_uuid + ".err"),
                                arcname=os.path.basename(master_jobs_list[completed_job_uuid][2]))
                        tar.close()

                    # Then delete the .out and .err files
                    os.remove(os.path.join(final_dir, completed_job_uuid + ".out"))
                    os.remove(os.path.join(final_dir, completed_job_uuid + ".err"))

            # Check if filtering is complete
            if completion_check:
                log("INFO", "Filtering Complete")
                return

            # Thread sleep before checking again
            time.sleep(0.5)

    def add_job(self, save_full_path, files):
        # Adds the job to the filter queue, starting filters if not already running
        if not self.status:
            # Setup the queues to pass messages
            self.jobQueue = Queue()
            self.messageQueue = Queue()

            # Create and start the filter runner
            self.filterRunner = Thread(target=self.filter_runner,
                                       args=(
                                           self.filter_base_dir,
                                           self.instance_list,
                                           self.jobQueue,
                                           self.messageQueue,))
            self.filterRunner.start()

            # Filters are now running, and will continue until the indexer has completed all jobs
            self.status = True

        # Add the job to the queue
        self.jobQueue.put([save_full_path, files])

    def filters_still_running(self):
        # Returns True if filters are still running or need to run, False if filters have completed work

        # Check if the filter system even ran
        if self.messageQueue is None:
            return False

        # If filters are still running, timeout checking begins
        if self.timeout_start is None:
            self.timeout_start = True

            # Send the timeout to the filter runner
            self.messageQueue.put('TIMEOUT_START')

        # Get the status based on the filter runner thread status
        self.status = self.filterRunner.is_alive()

        # Return the status back to the indexer
        return self.status

    def cleanup(self):
        # Executes when there are no more jobs
        if self.status is True:
            log("ERROR", "Filter cleanup when filters are still running")

        # Delete all temp filter input/output folders
        # (which should be empty unless there was an error in a filter's termination)
        try:
            shutil.rmtree(self.filter_base_dir)
        except OSError as e:
            log("ERROR", "When deleting the temporary filter processing folder, encountered an error: " + str(e))
