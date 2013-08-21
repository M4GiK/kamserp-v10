$(function () {
    $(document).on('click', 'button[name=subscribe]', function (e) {
        div = $(this).parent();
        parent = $(this).parent().parent();
        id = $(this).parent().parent().attr('id');
        openerp.jsonRpc('/recruitment/message_get_subscribed', 'call', {'email': $(this).siblings('input[name=email]').val(), 'id': id}).then(function (result) {
            if (result == 1) {
                div.hide();
                parent.find('.hidden').removeClass('hidden');
            }
        });
    });
    $(document).on('click', 'button[name=unsubscribe]', function (e) {
        div = $(this).parent();
        parent = $(this).parent().parent();
        id = $(this).parent().parent().attr('id');
        openerp.jsonRpc('/recruitment/message_get_unsubscribed', 'call', {'email': $(this).siblings('input[name=email]').val(), 'id': id}).then(function (result) {
            if (result == 1) {
                parent.find('.subscribedetails').show();
                div.addClass('hidden');
            }
        });
    });
    $(document).on('click', '.js_published, .js_unpublished', function (e) {
        e.preventDefault();
        var $link = $(this).parent();
        $link.find('.js_published, .js_unpublished').addClass("hidden");
        var $unp = $link.find(".js_unpublished");
        var $p = $link.find(".js_published");
        openerp.jsonRpc('/recruitment/published', 'call', {'id': $link.data('id'), 'object': $link.data('object')}).then(function (result) {
            if (+result['published']) {
                $p.addClass("hidden");
                $unp.removeClass("hidden");
                $('tr[id='+$link.data('id')+']').find('span#norecruit').addClass("hidden");
                $('tr[id='+$link.data('id')+']').find('span#counting').removeClass("hidden");
                if ($.trim($('tr[id='+$link.data('id')+']').find('span#counting').html()).length == 0) {
                    htmlcon = '<i class="icon-group"></i> No.of Post: <span id="counting_num">' + result['count'] + '</span>';
                    $('tr[id='+$link.data('id')+']').find('span#counting').html(htmlcon);
                } else {
                    $('tr[id='+$link.data('id')+']').find('span#counting').find('span#counting_num').html(result['count']);
                }
            } else {
                $p.removeClass("hidden");
                $unp.addClass("hidden");
                $('tr[id='+$link.data('id')+']').find('span#counting').addClass("hidden");
                $('tr[id='+$link.data('id')+']').find('span#norecruit').removeClass("hidden");
                if ($.trim($('tr[id='+$link.data('id')+']').find('span#norecruit').html()).length == 0) {
                    $('tr[id='+$link.data('id')+']').find('span#norecruit').html("Right now no recruitment is going on.")
                }
            }
        });
    });
});
