$(document).ready(function () {
    $('a.js_update_line_json').on('click', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var href = $link.attr("href");
        var order_id = href.match(/order_id=([0-9]+)/);
        var line_id = href.match(/update_line\/([0-9]+)/);
        var token = href.match(/token=(.*)/);
        openerp.jsonRpc("/quote/update_line/", 'call', {
                'line_id': line_id[1],
                'order_id': parseInt(order_id[1]),
                'token': token[1],
                'remove': $link.is('[href*="remove"]'),
                'unlink': $link.is('[href*="unlink"]')
                })
                .then(function (data) {
                    if(!data){
                        location.reload();
                    }
                    $link.parents('.input-group:first').find('.js_quantity').val(data[0]);
                    $('[data-id="total_amount"]>span').html(data[1]);
                });
        return false;
    });

    $('#modelaccept').on('shown.bs.modal', function (e) {
        $("#signature").empty().jSignature({'decor-color' : '#D1D0CE'});
    });

    $('#sign_clean').on('click', function (e) {
        $("#signature").jSignature('reset');
    });

    $('form.js_accept_json').submit(function(ev){
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var href = $link.attr("action");
        var order_id = href.match(/accept\/([0-9]+)/);
        var token = href.match(/token=(.*)/);

        var signer_name = $("#name").val();
        var sign = $("#signature").jSignature("getData",'image')[1];
        $('#signer').toggleClass('has-error', ! signer_name);
        $('#drawsign').toggleClass('panel-error', ! sign.length);

        if (! signer_name)
            return false;

        openerp.jsonRpc("/quote/accept/", 'call', {
            'order_id': parseInt(order_id[1]),
            'token': token[1],
            'signer': signer_name,
            'sign': sign?JSON.stringify(sign):false,
        }).then(function (data) {
            $('#modelaccept').modal('hide');
            window.location.replace(url +'/quote/'+order_id[1]+'/'+token[1]+'?message=3');
        });
        return false
    });

    // automatically generate a menu from h1 and h2 tag in content
    var ul = $('[data-id="quote_sidebar"]');
    var sub_li = null;
    var sub_ul = null;
    $("section h1, section h2").each(function() {
        switch (this.tagName.toLowerCase()) {
            case "h1":
                id = _.uniqueId('quote_header_')
                $(this.parentNode).attr('id',id);
                sub_li = $("<li>").html('<a href="#'+id+'">'+$(this).text()+'</a>').appendTo(ul);
                sub_ul = null;
                break;
            case "h2":
                id = _.uniqueId('quote_')
                if (sub_li) {
                    if (!sub_ul) {
                        sub_ul = $("<ul class='nav'>").appendTo(sub_li);
                    }
                    $(this.parentNode).attr('id',id)
                    $("<li>").html('<a href="#'+id+'">'+$(this).text()+'</a>').appendTo(sub_ul);
                }
                break;
            }
    });

});
