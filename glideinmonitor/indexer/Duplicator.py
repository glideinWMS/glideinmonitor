#Ethan Moon 6/19/22
import os
import shutil
import hashlib
import glob
import time
import argparse

#datetime .now

#logger 
#Make the hash function time based 
def genHash(filename: str, time2: int):
    return (hash(""+ filename + str(time2)))




#fuction that deletes the copy files in directory 
def deleter(directory_path):
    for filename in os.listdir(directory_path):
        if "copy" in filename:
            file_path = os.path.join(directory_path, filename)
            os.remove(file_path)
            print(f"Deleted: {file_path}")

    print("All files with 'copy' in their names have been removed.")


#Creates the copy of the files
def copier(multiples, path):

    #sanitization
    assert os.path.exists(path), "path does not exist"
    assert os.path.isdir(path), "path is not a directory"

    timeUpdate = time.time()
    #get all the job files in directory 
    list = glob.glob(path +"/*")

    #count how many files in list to get the

    
    refinedList = []
    #filter and adds all jobs to the refinedlist
    for p in list:
        if not "copy" in p:
            refinedList.append(p)

    #change the name and duplicate



    for i in range(multiples):
        for path in refinedList:

            try:
                filename = os.path.basename(path)
                file_extension = os.path.splitext(filename)[1]
                file_basename = os.path.splitext(filename)[0]
                file_hash = genHash(file_basename,timeUpdate)
                
                #changed to prevent really long names
                new_filename = f"{file_basename}_copy_{file_hash}_{i+1}{file_extension}"
                new_path = os.path.join(os.path.dirname(path), new_filename)
                shutil.copy2(path, new_path)
                print(f"File copied to {new_path}")
                print(f"Successfully copied the file {multiples} times.")

            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='multiplies or deletes files')
    parser.add_argument("action", choices=["add", "remove"], help="Specify whether to add or remove the file.")
    parser.add_argument("file_path", help="Specify the file path.")
    parser.add_argument("times", type=int, default=2, help="Number of times to copy the file (used with 'add' action).")
    args = parser.parse_args()

    if args.action == "add":
        copier(args.times, args.file_path)
    else:
        deleter(args.file_path)
     



    