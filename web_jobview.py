def jobview(jobID):
    data = ""
    with open('assets/jobview.html', 'r') as file:
        data = file.read()
    return data
