/*
* Helper functions
*/
function var_win(data, name) {
    // Open a variable's contents in a new window
    let newWindow = window.open("", name, "width=600, height=800");
    newWindow.document.write("<pre>" + data + "</pre>");
    newWindow.document.title = name;
}


function var_download(text, filename) {
    // Variable downloader
    let blob = new Blob([text], {type: "text/plain;charset=utf-8"});
    saveAs(blob, filename);
}


function parseTarString(text) {
    // Parses a inflated gzip file that's still in a tar? format
    // Returns a 2D array containing the name and text of each file
    let curr_file = -1;
    let content = [];

    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
        // For each line, check if the line is a TAR file header
        if (lines[i].includes(String.fromCharCode(0)) && lines[i].includes("ustar")) {
            // Increment the index of the content variable
            curr_file += 1;
            content[curr_file] = ["", ""];

            // Get the file name from the header
            let charStart = 0;
            while (lines[i].charCodeAt(charStart) === 0) {
                charStart += 1;
            }
            let begin_removed = lines[i].substr(charStart);
            content[curr_file][0] = begin_removed.substr(0, begin_removed.indexOf(String.fromCharCode(0)));

            // Get the last line of content (which is included on the same line of the 0 characters)
            content[curr_file][1] = lines[i].substring(1 + lines[i].lastIndexOf(String.fromCharCode(0))) + "\n";
        } else {
            content[curr_file][1] += lines[i] + "\n";
        }
    }

    return content;
}


function parseBase64(startText) {
    if (App.JobERR_Content.indexOf(startText) !== -1) {

        let begin = App.JobERR_Content.indexOf("644 -", App.JobERR_Content.indexOf(startText));
        if (begin !== -1) {
            begin = App.JobERR_Content.indexOf("644 -", begin) + 6;
            let end = App.JobERR_Content.indexOf("=", begin);
            let content = App.JobERR_Content.substr(begin, end - begin)
            return base64(content);
        }
    }
    return null;
}


function activateBtn(id, name, content) {
    // Enables a button with click support
    $("#" + id).addClass("btn-outline-primary");
    $("#" + id).removeClass("btn-outline-secondary");
    $("#" + id).removeAttr("disabled");
    $("#" + id).click(function () {
        btnClick(name, content)
    });
}


function btnClick(name, content) {
    // On button click, either open or download the content
    if ($("#toggleFileAction").parent().hasClass("off")) {
        // Download the content
        var_download(content, name);
    } else {
        // View the content
        var_win(content, name);
    }
}

/*
 * Search System
 */
function performSearch() {
    let query = $("#searchInput").val();
    if (query === "") {
        $("#searchTable").html("");
        return
    }

    let results = [];

    // Iterate over each file
    for (let file_index in App.JSON) {
        // Got a file, go through the contents
        const lines = App.JSON[file_index]["content"].split('\n');
        for (let i = 0; i < lines.length; i++) {
            if (lines[i].indexOf(query) !== -1) {
                // Found a line that matches the query
                results.push("<tr><td><pre>" + lines[i] + "</pre></td></tr>");
            }
        }
    }

    // Now add the results
    $("#searchTable").html(results);
}

/*
 * Initial Setup
 */
const App = new Vue({
    el: '#app',
    data: {
        job_id: null,
        content: "p { color : red }",
        infoTimestamp: null,
        infoTimestampH: null,
        infoInstanceName: null,
        infoEntryName: null,
        infoFileSize: null,
        infoFrontendUsername: null,
        infoGUID: null,
        infoEntry: null
    },
    mounted: function () {
        this.$nextTick(init(this));
    }
});

function init(App) {
    // Get the Job ID
    const urlPath = location.pathname;
    App.job_id = urlPath.split("/").pop();

    // Bind the (only) button we can
    $("#btnJobGZIP").click(function () {
        window.location = '/api/job_download/db_id/' + App.job_id;
    });
}


/*
 * Download: Job Info
 */
xhr_info = new XMLHttpRequest();
xhr_info.open('GET', '/api/job_info/db_id/' + App.job_id, true);

xhr_info.onload = function (e) {
    if (this.status === 200) {
        App.JobInfo = JSON.parse(this.response);

        App.infoInstanceName = App.JobInfo['InstanceName'];
        App.infoEntryName = App.JobInfo['EntryName'];
        App.infoFileSize = App.JobInfo['FileSize'];
        App.infoFrontendUsername = App.JobInfo['FrontendUsername'];
        App.infoGUID = App.JobInfo['GUID'];
        App.infoTimestamp = App.JobInfo['Timestamp'];
        App.infoTimestampH = moment.unix(App.JobInfo['Timestamp']).format();
    } else {
        alert("Error getting info file")
    }
};

xhr_info.send();

// Get the Data File itself and parse it
xhr_file = new XMLHttpRequest();
xhr_file.open('GET', '/api/job_download/db_id/' + App.job_id, true);
xhr_file.responseType = 'arraybuffer';

xhr_file.onload = function (e) {
    if (this.status === 200) {
        // Got it, now process the file
        App.InflatedZip = inflate(this.response);
        App.JSON = [];

        // Process individual files
        let files = parseTarString(App.InflatedZip);
        for (let i in files) {
            switch (files[i][0].substr(-3)) {
                case "out":
                    App.JobOUT_Name = files[i][0];
                    App.JobOUT_Content = files[i][1];
                    activateBtn("btnJobOUT", App.JobOUT_Name, App.JobOUT_Content);
                    App.JSON.push({name: App.JobOUT_Name, content: App.JobOUT_Content});
                    break;
                case "err":
                    App.JobERR_Name = files[i][0];
                    App.JobERR_Content = files[i][1];
                    activateBtn("btnJobERR", App.JobERR_Name, App.JobERR_Content);
                    App.JSON.push({name: App.JobERR_Name, content: App.JobERR_Content});
                    break;
            }
        }

        // Now process the err file for Condor Logs
        let fileNamePre = "job." + (App.job_id) + ".";

        if (App.JobERR_Name) {
            // Master Log
            App.JobCondorMasterLog = parseBase64("MasterLog\n========");
            if (App.JobCondorMasterLog) {
                activateBtn("btnMasterLog", fileNamePre + "MasterLog.txt", App.JobCondorMasterLog);
                App.JSON.push({name: fileNamePre + "MasterLog", content: App.JobCondorMasterLog});
            }

            // Startd Log
            App.JobCondorStartdLog = parseBase64("StartdLog\n========");
            if (App.JobCondorStartdLog) {
                activateBtn("btnStartdLog", fileNamePre + "StartdLog.txt", App.JobCondorStartdLog);
                App.JSON.push({name: fileNamePre + "StartdLog", content: App.JobCondorStartdLog});
            }

            // Starter Log
            App.JobCondorStarterLog = parseBase64("StarterLog\n========");
            if (App.JobCondorStarterLog) {
                activateBtn("btnStarterLog", fileNamePre + "StarterLog.txt", App.JobCondorStarterLog);
                App.JSON.push({name: fileNamePre + "StarterLog", content: App.JobCondorStarterLog});
            }

            // StartdHistory Log
            App.JobCondorStartdHistoryLog = parseBase64("StartdHistoryLog\n========");
            if (App.JobCondorStartdHistoryLog) {
                activateBtn("btnStardHistLog", fileNamePre + "StartdHistoryLog.txt", App.JobCondorStartdHistoryLog);
                App.JSON.push({
                    name: fileNamePre + "StartdHistoryLog",
                    content: App.JobCondorStartdHistoryLog
                });
            }

            // XML Description Log
            App.JobCondorXMLDescLog = parseBase64("=== Encoded XML description of glidein activity ===");
            if (App.JobCondorXMLDescLog) {
                activateBtn("btnXMLDescLog", fileNamePre + "XMLDescription.txt", App.JobCondorXMLDescLog);
                App.JSON.push({name: fileNamePre + "XMLDescription", content: App.JobCondorXMLDescLog});
            }
        }

        // Finally activate the JSON button
        activateBtn("btnJobJSON", fileNamePre + "json", JSON.stringify(App.JSON));
    } else {
        alert("Error downloading data file")
    }
};

xhr_file.send();
