import os


def jobview(jobID):
    data = ""
    with open(os.getcwd()+'\\web_interface\\assets\\jobview.html', 'r') as file:
        data = file.read()
    return data
