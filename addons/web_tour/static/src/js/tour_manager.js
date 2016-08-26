odoo.define('web_tour.TourManager', function(require) {
"use strict";

var core = require('web.core');
var local_storage = require('web.local_storage');
var Model = require('web.Model');
var session = require('web.session');
var Tip = require('web_tour.Tip');

var _t = core._t;

var RUNNING_TOUR_TIMEOUT = 10000;

function get_step_key(name) {
    return 'tour_' + name + '_step';
}
function get_running_key() {
    return 'running_tour';
}
function get_running_delay_key() {
    return get_running_key() + "_delay";
}

function do_before_unload(if_unload_callback, if_not_unload_callback) {
    if_unload_callback = if_unload_callback || function () {};
    if_not_unload_callback = if_not_unload_callback || if_unload_callback;

    var old_before = window.onbeforeunload;
    var reload_timeout;
    window.onbeforeunload = function () {
        clearTimeout(reload_timeout);
        window.onbeforeunload = old_before;
        if_unload_callback();
        if (old_before) return old_before.apply(this, arguments);
    };
    reload_timeout = _.defer(function () {
        window.onbeforeunload = old_before;
        if_not_unload_callback();
    });
}

var RunningTourActionHelper = core.Class.extend({
    init: function (tip_widget) {
        this.tip_widget = tip_widget;
    },
    click: function (element) {
        this._click(this._get_action_values(element));
    },
    text: function (text, element) {
        this._text(this._get_action_values(element), text);
    },
    drag_and_drop: function (to, element) {
        this._drag_and_drop(this._get_action_values(element), to);
    },
    keydown: function (keyCodes, element) {
        this._keydown(this._get_action_values(element), keyCodes.split(/[,\s]+/));
    },
    auto: function (element) {
        var values = this._get_action_values(element);
        if (values.consume_event === "input") {
            this._text(values);
        } else {
            this._click(values);
        }
    },
    _get_action_values: function (element) {
        var $element = element ? $(element).first() : this.tip_widget.$anchor;
        var consume_event = element ? Tip.getConsumeEventType($element) : this.tip_widget.consume_event;
        return {
            $element: $element,
            consume_event: consume_event,
        };
    },
    _click: function (values) {
        var href = values.$element.attr("href");
        if (href && href.length && href[0] !== "#" && values.$element.is("a") && href !== "javascript:void(0)") {
            window.location.href = href;
        } else {
            values.$element.trigger("mouseenter").mousedown().mouseup().click().trigger("mouseleave");
        }
    },
    _text: function (values, text) {
        this._click(values);

        text = text || "Test";
        if (values.consume_event === "input") {
            values.$element.trigger("keydown").val(text).trigger("keyup").trigger("input");
        } else if (values.$element.is("select")) {
            values.$element.children("option")
                .prop("selected", false).removeProp("selected")
                .filter(function () { return $(this).val() === text; })
                .prop("selected", true);
            this._click(values);
        } else {
            values.$element.text(text);
        }
        values.$element.trigger("change");
    },
    _drag_and_drop: function (values, to) {
        var $to = $(to || document.body);

        var elementCenter = values.$element.offset();
        elementCenter.left += values.$element.outerWidth()/2;
        elementCenter.top += values.$element.outerHeight()/2;

        var toCenter = $to.offset();
        toCenter.left += $to.outerWidth()/2;
        toCenter.top += $to.outerHeight()/2;

        values.$element.trigger($.Event("mousedown", {which: 1, pageX: elementCenter.left, pageY: elementCenter.top}));
        values.$element.trigger($.Event("mousemove", {which: 1, pageX: toCenter.left, pageY: toCenter.top}));
        values.$element.trigger($.Event("mouseup", {which: 1, pageX: toCenter.left, pageY: toCenter.top}));
    },
    _keydown: function (values, keyCodes) {
        while (keyCodes.length) {
            var keyCode = +keyCodes.shift();
            values.$element.trigger({type: "keydown", keyCode: keyCode});
            if ((keyCode > 47 && keyCode < 58) // number keys
                || keyCode === 32 // spacebar
                || (keyCode > 64 && keyCode < 91) // letter keys
                || (keyCode > 95 && keyCode < 112) // numpad keys
                || (keyCode > 185 && keyCode < 193) // ;=,-./` (in order)
                || (keyCode > 218 && keyCode < 223)) {   // [\]' (in order))
                document.execCommand("insertText", 0, String.fromCharCode(keyCode));
            }
            values.$element.trigger({type: "keyup", keyCode: keyCode});
        }
    },
});

return core.Class.extend({
    init: function(consumed_tours) {
        this.$body = $('body');
        this.active_tooltips = {};
        this.tours = {};
        this.consumed_tours = consumed_tours || [];
        this.running_tour = local_storage.getItem(get_running_key());
        this.running_step_delay = parseInt(local_storage.getItem(get_running_delay_key()), 10) || 300;
        this.TourModel = new Model('web_tour.tour');
        this.edition = (_.last(session.server_version_info) === 'e') ? 'enterprise' : 'community';
    },
    /**
     * Registers a tour described by the following arguments (in order)
     * @param [String] tour's name
     * @param [Object] dict of options (optional), available options are:
     *   test [Boolean] true if the tour is dedicated to tests (it won't be enabled by default)
     *   skip_enabled [Boolean] true to add a link to consume the whole tour in its tips
     *   url [String] the url to load when manually running the tour
     * @param [Array] dict of steps, each step being a dict containing a tip description
     */
    register: function() {
        var args = Array.prototype.slice.call(arguments);
        var last_arg = args[args.length - 1];
        var name = args[0];
        if (this.tours[name]) {
            console.warn(_.str.sprintf("Tour %s is already defined", name));
            return;
        }
        var options = args.length === 2 ? {} : args[1];
        var steps = last_arg instanceof Array ? last_arg : [last_arg];
        var tour = {
            name: name,
            steps: steps,
            url: options.url,
            test: options.test,
            wait_for: options.wait_for || $.when(),
        };
        if (options.skip_enabled) {
            tour.skip_link = '<p><span class="o_skip_tour">' + _t('Skip tour') + '</span></p>';
            tour.skip_handler = function (tip) {
                this._deactivate_tip(tip);
                this._consume_tour(name);
            };
        }
        this.tours[name] = tour;
    },
    _register_all: function (do_update) {
        if (this._all_registered) return;
        this._all_registered = true;

        _.each(this.tours, this._register.bind(this, do_update));
    },
    _register: function (do_update, tour, name) {
        if (tour.ready) return $.when();

        return tour.wait_for.then((function () {
            tour.current_step = parseInt(local_storage.getItem(get_step_key(name))) || 0;
            tour.steps = _.filter(tour.steps, (function (step) {
                return !step.edition || step.edition === this.edition;
            }).bind(this));

            tour.ready = true;

            if (do_update && (this.running_tour === name || (!this.running_tour && !tour.test && !_.contains(this.consumed_tours, name)))) {
                this._to_next_step(name, 0);
                this.update(name);
            }
        }).bind(this));
    },
    run: function (tour_name, step_delay) {
        if (this.running_tour) {
            this._deactivate_tip(this.active_tooltips[this.running_tour]);
            this._consume_tour(this.running_tour, _.str.sprintf("Killing tour %s", this.running_tour));
            return;
        }
        var tour = this.tours[tour_name];
        if (!tour) {
            console.warn(_.str.sprintf("Unknown Tour %s", name));
            return;
        }
        console.log(_.str.sprintf("Running tour %s", tour_name));
        this.running_tour = tour_name;
        this.running_step_delay = step_delay || this.running_step_delay;
        local_storage.setItem(get_running_key(), this.running_tour);
        local_storage.setItem(get_running_delay_key(), this.running_step_delay);

        this._deactivate_tip(this.active_tooltips[tour_name]);

        tour.current_step = 0;
        this._to_next_step(tour_name, 0);
        local_storage.setItem(get_step_key(tour_name), tour.current_step);

        if (tour.url) {
            this.pause();
            do_before_unload(null, (function () {
                this.play();
                this.update();
            }).bind(this));

            window.location.href = session.debug ? $.param.querystring(tour.url, {debug: session.debug}) : tour.url;
        } else {
            this.update();
        }
    },
    pause: function () {
        this.paused = true;
    },
    play: function () {
        this.paused = false;
    },
    /**
     * Checks for tooltips to activate (only from the running tour or specified tour if there
     * is one, from all active tours otherwise). Should be called each time the DOM changes.
     */
    update: function (tour_name) {
        if (this.paused) return;

        this.$modal_displayed = $('.modal:visible').last();

        tour_name = this.running_tour || tour_name;
        if (tour_name) {
            var tour = this.tours[tour_name];
            if (!tour || !tour.ready) return;

            if (this.running_tour && this.running_tour_timeout === undefined) {
                this._set_running_tour_timeout(this.running_tour, this.active_tooltips[this.running_tour]);
            }
            this._check_for_tooltip(this.active_tooltips[tour_name], tour_name);
        } else {
            _.each(this.active_tooltips, this._check_for_tooltip.bind(this));
        }
    },
    _check_for_tooltip: function (tip, tour_name) {
        var $trigger;
        if (tip.in_modal !== false && this.$modal_displayed.length) {
            $trigger = this.$modal_displayed.find(tip.trigger);
        } else {
            $trigger = $(tip.trigger);
        }
        $trigger = get_first_visible_element($trigger);
        var extra_trigger = tip.extra_trigger ? get_first_visible_element($(tip.extra_trigger)).length : true;
        var triggered = $trigger.length && extra_trigger;
        if (triggered) {
            if (!tip.widget) {
                this._activate_tip(tip, tour_name, $trigger);
            } else {
                tip.widget.update($trigger);
            }
        } else {
            this._deactivate_tip(tip);
        }

        function get_first_visible_element($elements) {
            for (var i = 0 ; i < $elements.length ; i++) {
                var $i = $elements.eq(i);
                if ($i.is(":visible") && _has_visibility($i)) {
                    return $i;
                }
            }
            return $();

            function _has_visibility($elem) {
                if ($elem.css("visibility") === "hidden") {
                    return false;
                }
                if ($elem.is("html")) {
                    return true;
                }
                return _has_visibility($elem.parent());
            }
        }
    },
    _activate_tip: function(tip, tour_name, $anchor) {
        var tour = this.tours[tour_name];
        var tip_info = tip;
        if (tour.skip_link) {
            tip_info = _.extend(_.omit(tip_info, 'content'), {
                content: tip.content + tour.skip_link,
                event_handlers: [{
                    event: 'click',
                    selector: '.o_skip_tour',
                    handler: tour.skip_handler.bind(this, tip),
                }],
            });
        }
        tip.widget = new Tip(this, tip_info);
        if (this.running_tour !== tour_name) {
            tip.widget.on('tip_consumed', this, this._consume_tip.bind(this, tip, tour_name));
        }
        tip.widget.attach_to($anchor).then(this._to_next_running_step.bind(this, tip, tour_name));
    },
    _deactivate_tip: function(tip) {
        if (tip && tip.widget) {
            tip.widget.destroy();
            delete tip.widget;
        }
    },
    _consume_tip: function(tip, tour_name) {
        this._deactivate_tip(tip);
        this._to_next_step(tour_name);

        var is_running = (this.running_tour === tour_name);
        if (is_running) {
            console.log(_.str.sprintf("Tour %s: step %s succeeded", tour_name, tip.trigger));
        }

        if (this.active_tooltips[tour_name]) {
            local_storage.setItem(get_step_key(tour_name), this.tours[tour_name].current_step);
            if (is_running) {
                this._set_running_tour_timeout(tour_name, this.active_tooltips[tour_name]);
            }
            this.update(tour_name);
        } else {
            this._consume_tour(tour_name);
        }
    },
    _to_next_step: function (tour_name, inc) {
        var tour = this.tours[tour_name];
        tour.current_step += (inc !== undefined ? inc : 1);
        if (this.running_tour !== tour_name) {
            var index = _.findIndex(tour.steps.slice(tour.current_step), function (tip) {
                return !tip.auto;
            });
            if (index >= 0) {
                tour.current_step += index;
            } else {
                tour.current_step = tour.steps.length;
            }
        }
        this.active_tooltips[tour_name] = tour.steps[tour.current_step];
    },
    _consume_tour: function (tour_name, error) {
        delete this.active_tooltips[tour_name];
        this.tours[tour_name].current_step = 0;
        local_storage.removeItem(get_step_key(tour_name));
        if (this.running_tour === tour_name) {
            this._stop_running_tour_timeout();
            local_storage.removeItem(get_running_key());
            local_storage.removeItem(get_running_delay_key());
            this.running_tour = undefined;
            this.running_step_delay = undefined;
            if (error) {
                console.log("error " + error); // phantomJS wait for message starting by error
            } else {
                console.log(_.str.sprintf("Tour %s succeeded", tour_name));
                console.log("ok"); // phantomJS wait for exact message "ok"
            }
        } else {
            this.TourModel.call('consume', [[tour_name]]).then((function () {
                this.consumed_tours.push(tour_name);
            }).bind(this));
        }
    },
    _set_running_tour_timeout: function (tour_name, step) {
        this._stop_running_tour_timeout();
        this.running_tour_timeout = setTimeout((function() {
            this._consume_tour(tour_name, _.str.sprintf("Tour %s failed at step %s", tour_name, step.trigger));
        }).bind(this), RUNNING_TOUR_TIMEOUT + this.running_step_delay);
    },
    _stop_running_tour_timeout: function () {
        clearTimeout(this.running_tour_timeout);
        this.running_tour_timeout = undefined;
    },
    _to_next_running_step: function (tip, tour_name) {
        if (this.running_tour !== tour_name) return;
        this._stop_running_tour_timeout();

        var action_helper = new RunningTourActionHelper(tip.widget);
        _.delay((function () {
            do_before_unload(this._consume_tip.bind(this, tip, tour_name));

            if (typeof tip.run === "function") {
                tip.run.call(tip.widget, action_helper);
            } else if (tip.run !== undefined) {
                var m = tip.run.match(/^([a-zA-Z0-9_]+) *(?:\(? *(.+?) *\)?)?$/);
                action_helper[m[1]](m[2]);
            } else {
                action_helper.auto();
            }
        }).bind(this), this.running_step_delay);
    },

    /**
     * Tour predefined steps
     */
    STEPS: {
        MENU_MORE: {
            edition: "community",
            trigger: "body > nav",
            position: "bottom",
            auto: true,
            run: function (actions) {
                actions.auto("#menu_more_container > a");
            },
        },

        TOGGLE_APPSWITCHER: {
            edition: "enterprise",
            trigger: ".o_main_navbar .o_menu_toggle",
            content: _t('Click the <i>Home icon</i> to navigate across apps.'),
            position: "bottom",
        },

        WEBSITE_NEW_PAGE: {
            trigger: "#oe_main_menu_navbar a[data-action=new_page]",
            auto: true,
            position: "bottom",
        },
    },
});

});
