from database import Database


def genTable():
    # Connect to the database (will setup if not existing)
    db = Database()

    table_raw = db.output_table()

    db.quit()

    table_output = ""
    i = 0
    for curr in table_raw:
        i += 1
        if i > 100: break
        table_output += "<tr><td><a href=\"/job/{}\">{}</a></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            curr[0], curr[1], curr[2], curr[3], curr[4])
    return table_output


def homepage():
    html_content = """<!DOCTYPE html>
<html>
<body>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/v/dt/jq-3.3.1/dt-1.10.18/datatables.min.css"/>
 
<script type="text/javascript" src="https://cdn.datatables.net/v/dt/jq-3.3.1/dt-1.10.18/datatables.min.js"></script>

<table id="example" class="display" style="width:100%">
        <thead>
            <tr>
                <th>JobID</th>
                <th>FileSize</th>
                <th>InstanceName</th>
                <th>Username</th>
            </tr>
        </thead>
        <tbody>
            """ + genTable() + """
        </tbody>
        <tfoot>
            <tr>
                <th>JobID</th>
                <th>FileSize</th>
                <th>InstanceName</th>
                <th>Username</th>
            </tr>
        </tfoot>
    </table>
    
    <script>
    $(document).ready(function() {
    $('#example').DataTable();
} );
    </script>
</body>
</html>
"""

    return html_content
