odoo.define('web.GraphView', function (require) {
"use strict";
/*---------------------------------------------------------
 * Odoo Graph view
 *---------------------------------------------------------*/

var core = require('web.core');
var GraphWidget = require('web.GraphWidget');
var Model = require('web.Model');
var View = require('web.View');

var _lt = core._lt;
var _t = core._t;
var QWeb = core.qweb;

var GraphView = View.extend({
    className: 'oe_graph',
    display_name: _lt('Graph'),
    view_type: 'graph',

    init: function(parent, dataset, view_id, options) {
        this._super(parent, dataset, view_id, options);

        this.model = new Model(dataset.model, {group_by_no_leaf: true});
        this.measures = [];
        this.active_measure = '__count__';
        this.initial_groupbys = [];
        this.widget = undefined;
    },
    start: function () {
        var load_fields = this.model.call('fields_get', [])
                .then(this.prepare_fields.bind(this));

        return $.when(this._super(), load_fields).then(this.render_buttons.bind(this));
    },
    render_buttons: function () {
        // Render buttons only in non-headless mode as buttons are in the header
        if (!this.options.headless) {
            var context = {measures: _.pairs(_.omit(this.measures, '__count__'))};
            this.$buttons.html(QWeb.render('GraphView.buttons', context));
            this.$measure_list = this.$buttons.find('.oe-measure-list');
            this.update_measure();
            this.$buttons.find('button').tooltip();
            this.$buttons.click(this.on_button_click.bind(this));
        }
    },
    update_measure: function () {
        var self = this;
        this.$measure_list.find('li').each(function (index, li) {
            $(li).toggleClass('selected', $(li).data('field') === self.active_measure);
        });
    },
    view_loading: function (fvg) {
        var self = this;
        fvg.arch.children.forEach(function (field) {
            var name = field.attrs.name;
            if (field.attrs.interval) {
                name += ':' + field.attrs.interval;
            }
            if (field.attrs.type === 'measure') {
                self.active_measure = name;
            } else {
                self.initial_groupbys.push(name);
            }
        });
    },
    do_show: function () {
        this.do_push_state({});
        this.$el.show();
        return this._super();
    },
    prepare_fields: function (fields) {
        var self = this;
        this.fields = fields;
        _.each(fields, function (field, name) {
            if ((name !== 'id') && (field.store === true)) {
                if (field.type === 'integer' || field.type === 'float') {
                    self.measures[name] = field;
                }
            }
        });
        this.measures.__count__ = {string: _t("Quantity"), type: "integer"};
    },
    do_search: function (domain, context, group_by) {
        if (!this.widget) {
            this.initial_groupbys = context.graph_groupbys || this.initial_groupbys;
            this.widget = new GraphWidget(this, this.dataset.model, {
                measure: context.graph_measure || this.active_measure,
                mode: context.graph_mode || this.active_mode,
                domain: domain,
                groupbys: this.initial_groupbys,
                context: context,
                fields: this.fields,
            });
            // append widget
            this.$el.hide();
            this.widget.appendTo(this.$el);
        } else {
            var groupbys = group_by.length ? group_by : this.initial_groupbys.slice(0);
            this.widget.update_data(domain, groupbys);
        }
    },
    get_context: function () {
        return !this.widget ? {} : {
            graph_mode: this.widget.mode,
            graph_measure: this.widget.measure,
            graph_groupbys: this.widget.groupbys
        };
    },
    on_button_click: function (event) {
        var $target = $(event.target);
        if ($target.hasClass('oe-bar-mode')) {this.widget.set_mode('bar');}
        if ($target.hasClass('oe-line-mode')) {this.widget.set_mode('line');}
        if ($target.hasClass('oe-pie-mode')) {this.widget.set_mode('pie');}
        if ($target.parents('.oe-measure-list').length) {
            var parent = $target.parent(),
                field = parent.data('field');
            this.active_measure = field;
            parent.toggleClass('selected');
            event.stopPropagation();
            this.update_measure();
            this.widget.set_measure(this.active_measure);
        }
    },
});

core.view_registry.add('graph', GraphView);

return GraphView;

});
