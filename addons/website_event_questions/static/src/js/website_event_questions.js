odoo.define('website_event_questions.website_event_questions', function (require) {
var event_registration_form = require('website_event.website_event');
'use strict';

event_registration_form.EventRegistrationForm.include({
    on_click: function(ev) {
        var def = this._super.apply(this, arguments);
        def.then(function() {
            $("select.o_specific_answer,select.o_general_answer").each(function(index, elem) {
                $(elem).select2({ minimumResultsForSearch: -1, width: '100%' });
            });
        });
    }
});
});