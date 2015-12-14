(function($) {
    $(document).ready(function() {
        $('#user_id').change(function() {
            var selected_user = $("#user_id").val(),
                image = $("#image");
            image.hide();
            $.getJSON("/api/v2/users/"+selected_user, function(result) {
                image.empty();
                image.append("<img src='"+result.link_to_avatar+"' />");
            });
            image.show();
        });
    });
})(jQuery);
