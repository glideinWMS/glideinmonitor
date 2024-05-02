#Purpose is to run the profiler on a certain amount of files and track the data on a csv file/ dataset or just print it 

import subprocess
import pstats
import argparse
import glob

#Removes the duplicated logs in the directory
def removeDuplicatedLogs ():

    command = [
        "python3",
        "/opt/GlideinWMS/glideinmonitor/glideinmonitor/indexer/Duplicator.py",
        "remove",
        "/etc/glideinmonitor/debug/client/user_frontend/glidein_gfactory_instance/entry_ce-workspace.fnal.gov",
        "2"
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running the command: {e}")



#Adds the new duplicated jobs 
def jobsMultipier (times):

    #Adds Files 
    command = [
            "python3",
            "/opt/GlideinWMS/glideinmonitor/glideinmonitor/indexer/Duplicator.py",
            "add",
            "/etc/glideinmonitor/debug/client/user_frontend/glidein_gfactory_instance/entry_ce-workspace.fnal.gov",
            str(times)
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
       print(f"Error running the command: {e}")



#generates the text file profilerTimes.txt with 
def createDataPoint(samples):
 #Data point loop
   

    with open('profilerTimes.csv', 'a') as file:
        
        #dataPoints 
        timeReadings=[]

        try:
            result = subprocess.check_output("ls /etc/glideinmonitor/debug/client/user_frontend/glidein_gfactory_instance/entry_ce-workspace.fnal.gov | wc -l", shell=True, text=True)
            result=result.strip()
            final_result = (int(result)/2)

        except subprocess.CalledProcessError as e:
            print(f"Error running the command: {e}")
            final_result = ""

        timeReadings.append(str(final_result))

        for cmd in [["python3", "indexer.py", "-z"], ["python3", "indexer.py"]]:

            for compress in range(samples):

                # Runs the clean up
                shell_script = "cleanUp.sh"
                try:
                    subprocess.run(["bash", shell_script], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error running {shell_script}: {e}")

                #Runs indexer
                subprocess.run(cmd)

                #after running indexer 
                loadedStats = pstats.Stats("savedStat")
                recordedTime = str(loadedStats.total_tt)

                #transfers cumTime to the File
                timeReadings.append(recordedTime)
        file.write(",".join(timeReadings)+'\n')

def setup_file (samples):
     #clears the file
    with open('profilerTimes.csv', 'w') as _:
        pass


    # Creates the title for the file ProfilerTimes
    title = "Num_Jobs,"
    for x in range(samples):
        title+= "Compress Time " + str(x+1)
    for x in range(samples):
        title+= "Non " + str(x+1)

    #writes the title to the file
    with open('profilerTimes.csv', 'w') as file:
       file.write(title + '\n')

def main (starting_jobs,samples,increments,jobs_limit):
    
    setup_file(samples)
    removeDuplicatedLogs()
    jobsMultipier(starting_jobs-1)
    createDataPoint(samples)

    for _ in range (int((jobs_limit-starting_jobs)/increments)):

        jobsMultipier(increments)
        createDataPoint(samples)
        



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='multiplies or deletes files')

    #number times 4 for original value
    parser.add_argument("--starting-jobs", type=int, default=2, help="Number of original jobs you would want (ex. 100,1000, etc.)")

    #number of data points per file size and compress/Non
    parser.add_argument("--samples", type=int, default=2, help="Number of samples per configuration per data point.")


    #how fast to get to upper limit 
    #if there are 100 files increase by 100 so the next test would be 200
    parser.add_argument("--increments", type=int, default=10, help="Increments that the file should increase by")

    #upper limit 
    parser.add_argument("--jobs-limit", type=int, default=10, help="Upper limit that increments go up to ")

    args = parser.parse_args()

    main(args.starting_jobs,args.samples, args.increments, args.jobs_limit)

