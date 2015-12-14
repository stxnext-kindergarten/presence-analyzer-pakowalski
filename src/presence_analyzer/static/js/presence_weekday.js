google.load("visualization", "1", {packages:["corechart"], 'language': 'en'});

(function($) {
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
                $.getJSON("/api/v1/presence_weekday/"+selected_user, function(result) {
                    var data = google.visualization.arrayToDataTable(result),
                        options = {};
                    chart_div.show();
                    loading.hide();
                    var chart = new google.visualization.PieChart(chart_div[0]);
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
