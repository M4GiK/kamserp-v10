{
    "name" : "web",
    "category" : "Hidden",
    "depends" : [],
    'active': True,
    'post_load' : 'wsgi_postload',
    'js' : [
        "static/lib/datejs/globalization/en-US.js",
        "static/lib/datejs/core.js",
        "static/lib/datejs/parser.js",
        "static/lib/datejs/sugarpak.js",
        "static/lib/datejs/extras.js",
        "static/lib/jquery/jquery-1.6.2.js",
        "static/lib/jquery.MD5/jquery.md5.js",
        "static/lib/jquery.form/jquery.form.js",
        "static/lib/jquery.validate/jquery.validate.js",
        "static/lib/jquery.ba-bbq/jquery.ba-bbq.js",
        "static/lib/jquery.contextmenu/jquery.contextmenu.r2.packed.js",
        "static/lib/jquery.blockUI/jquery.blockUI.js",
        "static/lib/jquery.superfish/js/hoverIntent.js",
        "static/lib/jquery.superfish/js/superfish.js",
        "static/lib/jquery.ui/js/jquery-ui-1.8.9.custom.min.js",
        "static/lib/jquery.ui/js/jquery-ui-timepicker-addon.js",
        "static/lib/jquery.ui.notify/js/jquery.notify.js",
        "static/lib/jquery.deferred-queue/jquery.deferred-queue.js",
        "static/lib/jquery.scrollTo/jquery.scrollTo-min.js",
        "static/lib/jquery.tipTip/jquery.tipTip.js",
        "static/lib/json/json2.js",
        "static/lib/qweb/qweb2.js",
        "static/lib/underscore/underscore.js",
        "static/lib/underscore/underscore.string.js",
        "static/lib/labjs/LAB.src.js",
        "static/lib/py.parse/lib/py.js",
        "static/src/js/jq_ajax.js",
        "static/src/js/boot.js",
        "static/src/js/core.js",
        "static/src/js/dates.js",
        "static/src/js/formats.js",
        "static/src/js/chrome.js",
        "static/src/js/views.js",
        "static/src/js/data.js",
        "static/src/js/data_export.js",
        "static/src/js/data_import.js",
        "static/src/js/search.js",
        "static/src/js/view_form.js",
        "static/src/js/view_list.js",
        "static/src/js/view_list_editable.js",
        "static/src/js/view_tree.js",
        "static/src/js/view_editor.js",
        "static/src/js/embed.js",
    ],
    'css' : [
        "static/lib/jquery.superfish/css/superfish.css",
        "static/lib/jquery.ui/css/smoothness/jquery-ui-1.8.9.custom.css",
        "static/lib/jquery.ui.notify/css/ui.notify.css",
        "static/lib/jquery.tipTip/tipTip.css",
        "static/src/css/base.css",
        "static/src/css/data_export.css",
        "static/src/css/data_import.css",
    ],
    'qweb' : [
        "static/src/xml/*.xml",
    ],
}
