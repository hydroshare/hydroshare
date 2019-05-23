function initializeTable() {
    var ACCESSED_COL = 0;
    var TITLE_COL = 1;
    var FIRST_AUTHOR_COL = 2;
    var RESOURCE_TYPE_COL = 3;
    var VISIBILITY_COL = 4;

    var colDefs = [
        {
            "targets": [ACCESSED_COL],
            "width": "100px"
        },
        {
            "targets": [ TITLE_COL],
            "width": "500px"
        },
        {
            "targets": [FIRST_AUTHOR_COL],
            "width": "100px"
        },
        {
            "targets": [RESOURCE_TYPE_COL],
            "width": "100px"
        },
        {
            "targets": [VISIBILITY_COL],
            "width": "50px"
        },
    ];

    $('#recently-visited-resources').DataTable({
        "paging": false,
        "searching": false,
        "info": false,
        "ordering": false,
        "lengthChange": false,
        "columnDefs": colDefs,
        "language": {
            "emptyTable": "Visit or create resources to populate this table."
        }
    });

}

$(document).ready(function () {
    initializeTable();

    if (localStorage.openStatus === "closed") {
        $("#getStarted").addClass("collapse");
        $("#id-getting-started-toggle").html("Show Getting Started");
    } else if (localStorage.openStatus === "opened") {
        $("#getStarted").addClass("in");
        $("#id-getting-started-toggle").html("Hide Getting Started");
    } else {
        $("#getStarted").addClass("in");
        $("#id-getting-started-toggle").html("Hide Getting Started");
    }
    // add action handler
    $("#id-getting-started-toggle").click(function () {
        $("#id-getting-started-toggle").text(function (i, old) {
            var statusChangedTo = old === 'Show Getting Started' ? 'Hide Getting Started' : 'Show Getting Started';

            if (statusChangedTo === "Hide Getting Started") {
                localStorage.openStatus = "opened";
            } else if (statusChangedTo === "Show Getting Started") {
                localStorage.openStatus = "closed";
            } else {
                localStorage.openStatus = "opened";
            }
            return statusChangedTo;
        });
    });
});

