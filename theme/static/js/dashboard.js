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
        $("#change_me").html("Show get started");
    } else if (localStorage.openStatus === "opened") {
        $("#getStarted").addClass("in");
        $("#change_me").html("Hide get started");
    } else {
        $("#getStarted").addClass("in");
        $("#change_me").html("Hide get started");
    }
    // add action handler
    $("#change_me").click(function () {
        $("#change_me").text(function (i, old) {
            var statusChangedTo = old === 'Show get started' ? 'Hide get started' : 'Show get started';

            if (statusChangedTo === "Hide get started") {
                localStorage.openStatus = "opened";
            } else if (statusChangedTo === "Show get started") {
                localStorage.openStatus = "closed";
            } else {
                localStorage.openStatus = "opened";
            }
            return statusChangedTo;
        });
    });
});

