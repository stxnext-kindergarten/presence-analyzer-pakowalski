google.load("visualization", "1", {packages:["bar"], 'language': 'pl'});

(function($) {
    function parseInterval(value) {
        return value / 3600
    }
    $(document).ready(function() {
        var loading = $('#loading');
        $.getJSON("/api/v2/users", function(result) {
            var dropdown = $("#user_id");
            $.each(result, function(item) {
                dropdown.append($("<option />").val(item).text(this.user_name));
            });
            dropdown.show();
            loading.hide();
        });
        $('#user_id').change(function() {
            var selected_user = $("#user_id").val(),
                chart_div = $('#chart_div');
            if (selected_user) {
                loading.show();
                chart_div.hide();
                $.getJSON("/api/v1/top5/"+selected_user, function(result) {
                    $.each(result, function(index, value) {
                        value[1] = parseInterval(value[1]);
                    });
                    var data = new google.visualization.DataTable();
                    data.addColumn('string', 'Week');
                    data.addColumn('number', 'Hours');
                    data.addRows(result);
                    var options = {
                      width: 780,
                      legend: {position: 'none'},
                      axes: {
                        x: {0: {side: 'down', label: 'Weeks'}},
                        y: {0: {side: 'top', label: 'Hours'}}
                      },
                      bar: {groupWidth: "35%"}
                    },
                        chart = new google.charts.Bar(document.getElementById('chart_div'));
                    chart.draw(data, google.charts.Bar.convertOptions(options));
                    chart_div.show();
                    loading.hide();
                    var chart = new google.visualization.ColumnChart(chart_div[0]);
                    chart.draw(data, options);
                }).fail(function() {
                    chart_div.empty();
                    chart_div.append("No data");
                    chart_div.show();
                    loading.hide();
                });
            }
        });
    });
})(jQuery);
