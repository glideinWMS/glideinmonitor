const App = new Vue({
    el: '#app',
    data: {
        table_loading: true
    },
    mounted: function () {
        this.$nextTick(init(this));
    }
});

// --When-- IF an error happens
function error(text) {
    $("#errorModalText").text(text);
    $("#errorModal").modal();
}


function init(App) {
    /* ##########################################
     * Entries Dropdown Selection Population
     * ##########################################
     */

    var request = new XMLHttpRequest();
    request.open("GET", '/api/entries');
    request.onreadystatechange = function () {
        if (request.readyState === 4 && request.status === 200) {
            $.each(JSON.parse(request.response), function (key, value) {
                // noinspection JSCheckFunctionSignatures
                $('#select_entry_name')
                    .append($("<option selected></option>")
                        .attr("value", key)
                        .text(value));
            });
        } else if (request.readyState === 4) {
            error("There was an error getting a list of available entries")
        }
    };
    request.send(null);


    /* ##########################################
     * Datetime Setup
     * ##########################################
     */

    $('#datetime_from').datetimepicker({
        useCurrent: false
    });
    $('#datetime_to').datetimepicker({
        useCurrent: false
    });
    $("#datetime_from").on("change.datetimepicker", function (e) {
        $('#datetime_to').datetimepicker('minDate', e.date);
    });
    $("#datetime_to").on("change.datetimepicker", function (e) {
        $('#datetime_from').datetimepicker('maxDate', e.date);
    });

    $('.my-select').selectpicker();

    // Clear (needed since bound to each other)
    $("#datetime_from_clear").click(function () {
        $('#datetime_from').datetimepicker('clear');
        $('#datetime_from').datetimepicker('destroy');


        $('#datetime_from').datetimepicker({
            useCurrent: false
        });

        $('#datetime_to').datetimepicker('minDate', false);
    });

    $("#datetime_to_clear").click(function () {
        $('#datetime_to').datetimepicker('clear');
        $('#datetime_to').datetimepicker('destroy');


        $('#datetime_to').datetimepicker({
            useCurrent: false
        });

        $('#datetime_from').datetimepicker('maxDate', false);
    });


    /* ##########################################
     * DataTable Setup
     * ##########################################
     */
    App.table_data = {};
    App.table = $('#main_table').DataTable({
        "scrollX": true,
        buttons: ['copy', 'excel', 'print'],
        colReorder: true,
        keys: true,
        "initComplete": function () {
            // Add buttons
            App.table.buttons(0, null).containers().appendTo($('#table_buttons'));

            // Click to format table
            setTimeout(function () {
                $("#main_table_wrapper .table .sorting").click()
            }, 10);
        },
        "ajax": {
            "url": "/api/job_search",
            "type": "POST",
            "data": function (d) {
                return $.extend(d, App.table_data);
            },
            "dataSrc": function (json) {
                // Check if there are 50k rows (if so, it probably got limited from the server)
                if (json.data.length === 50000) {
                    alert("50k Row Limit Reached, narrow down search to include all results");
                }

                // Modify data once it's given from the server
                for (row of json.data) {
                    // Make the JobID clickable to a job view
                    row[1] = "<a href=\"job/" + row[0] + "\">" + row[1] + "</a>";
                    row.shift();

                    // Make the timestamp human readable
                    row[2] = moment.unix(row[2]).format();
                }

                App.table_loading = false;
                return json.data;
            }
        }
    });

    // Bind submit button for data tables
    $("#search").click(function () {
        // Get Timestamps
        from_timestamp = "";
        to_timestamp = "";
        if ($("#datetime_from_input").val()) {
            from_timestamp = $('#datetime_from').datetimepicker('viewDate').unix();
        }

        if ($("#datetime_to_input").val()) {
            to_timestamp = $('#datetime_to').datetimepicker('viewDate').unix();
        }

        // Get Entries
        entries = [];
        $("#select_entry_name").find('option:selected').each(function (index) {
            entries.push($(this).text())
        });
        entries = JSON.stringify(entries);

        // Setup the new request and then reload
        App.table_data = {
            "timestamp_from": from_timestamp,
            "timestamp_to": to_timestamp,
            "entries": entries
        };

        App.table.ajax.reload();
    });
}
