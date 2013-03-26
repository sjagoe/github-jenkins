$(document).ready(function() {
    var base_delay = 60000;
    var delay;
    var make_short_delay = function () {
        return base_delay + (Math.random() * base_delay);
    };
    $("#pull-request-table-body").data("update-url", "new/0/");

    function replace_row(row_element, json) {
        tr = $("<tr id=\"" + json.pr_id + "\"></tr>");
        tr.append("<td><a href=\"" + json.pr_issue_url + "\">" + json.pr_number + "</a></td>");
        tr.append("<td>" + json.pr_title + "</td>");
        if (json.build_number === null) {
            tr.append("<td/>");
        } else {
            tr.append("<td><a href=\"" + json.build_url + "\">" + json.build_number + "</a></td>");
        };
        if (json.build_status === null) {
            tr.append("<td/>");
        } else {
            tr.append("<td>" + json.build_status + "</td>");
        };
        tr.append("<td><a href=\"" + json.build_now_url + "\">Build now</a></td>");

        row_element.replaceWith(tr);

        return tr;
    };

    function get_new_pull_requests() {
        var update_url = $("#pull-request-table-body").data("update-url");
        $.getJSON(update_url)
            .done(function(json) {
                $("#pull-request-table-body").data("update-url", json.update_url);
                var previous_row = $("#pull-request-table-body tr:first");
                $.each(json.rows, function(index, elem) {
                    if (elem.open === true) {
                        var placeholder = $("<tr id=\"" + elem.pr_id + "\"></tr>").insertAfter(previous_row);

                        var new_row = replace_row(placeholder, elem);

                        var reload_this_row = function() {
                            $.get(elem.update_url)
                                .done(function(data) {
                                    if (data.open === true) {
                                        replace_row($("#" + data.pr_id), data);
                                        var delay = make_short_delay();
                                        window.setTimeout(reload_this_row, delay);
                                    } else {
                                        $("#" + data.pr_id).remove();
                                    };
                                })
                                .fail(function() {
                                    var delay = make_short_delay();
                                    window.setTimeout(reload_this_row, delay);
                                });
                        };
                        var delay = make_short_delay();
                        window.setTimeout(reload_this_row, delay);

                        previous_row = new_row;
                    };
                });
                var delay = make_short_delay();
                window.setTimeout(get_new_pull_requests, delay);
            })
            .fail(function() {
                var delay = make_short_delay();
                window.setTimeout(get_new_pull_requests, delay);
            });
    };
    get_new_pull_requests();
});
