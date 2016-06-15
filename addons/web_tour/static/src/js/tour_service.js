odoo.define('web_tour.tour', function(require) {
"use strict";

var ajax = require('web.ajax');
var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var TourManager = require('web_tour.TourManager');

var QWeb = core.qweb;

if (config.device.size_class <= config.device.SIZES.XS) { return; }

return session.is_bound.then(function () {
    var template_def;
    if (session.is_frontend && session.is_admin) {
        // Manually load tip template if we are in the frontend, as admin
        template_def = ajax.loadXML('/web_tour/static/src/xml/tip.xml', QWeb);
    }
    return $.when(template_def).then(function () {
        var tour = new TourManager(session.web_tours);

        // Use a MutationObserver to detect DOM changes
        var untracked_classnames = ["o_tooltip", "o_tooltip_content", "o_tooltip_overlay"];
        var check_tooltip = _.throttle(function (records) {
            var update = _.find(records, function (record) {
                var record_class = record.target.className;
                return !_.isString(record_class) ||
                       _.intersection(record_class.split(' '), untracked_classnames).length === 0;
            });
            if (update) { // ignore mutations in the tooltip itself
                tour.update();
            }
        }, 500, {leading: false});
        var observer = new MutationObserver(check_tooltip);
        var observe = observer.observe.bind(observer, document.body, {
            attributes: true,
            childList: true,
            subtree: true,
        });

        // Enable the MutationObserver for the admin or if a tour is running, when the DOM is ready
        if (session.is_admin || tour.running_tour) {
            $(observe);
        }
        // Override the TourManager so that it enables/disables the observer when necessary
        if (!session.is_admin) {
            var run = tour.run;
            tour.run = function () {
                run.apply(this, arguments);
                if (this.running_tour) { observe(); }
            };
            var _consume_tour = tour._consume_tour;
            tour._consume_tour = function () {
                _consume_tour.apply(this, arguments);
                observer.disconnect();
            };
        }

        return tour;
    });
});

});
